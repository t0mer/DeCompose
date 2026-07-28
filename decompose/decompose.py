import os, re, uvicorn, docker
import pyaml
from collections import OrderedDict
from loguru import logger
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import FileResponse

# Container names are constrained by Docker to this character set; validate the
# user-supplied `cname` against it on every endpoint so malformed input is
# rejected at the boundary instead of flowing into downstream lookups.
CNAME_RE = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9_.\-]*')


def validate_cname(cname):
    if not cname or not CNAME_RE.fullmatch(cname):
        raise HTTPException(status_code=400, detail="Invalid container name")


def main(cname):
    struct = {}
    networks = []
    cfile, networks = generate(cname)
    struct.update(cfile)
    return render(struct, networks)


def render(struct, networks):
    compose = OrderedDict({'version': '"3"', 'services': struct, 'networks': networks})
    return compose


def generate(cname):
    c = docker.from_env()

    try:
        cid = [x.short_id for x in c.containers.list(all=True) if cname == x.name or cname == x.short_id][0]
    except IndexError:
        raise HTTPException(status_code=404, detail=f"Container '{cname}' not found")

    cattrs = c.containers.get(cid).attrs


    # Build yaml dict structure

    cfile = {}
    cfile[cattrs['Name'][1:]] = {}
    ct = cfile[cattrs['Name'][1:]]

    values = {
        'cap_add': cattrs['HostConfig']['CapAdd'],
        'cap_drop': cattrs['HostConfig']['CapDrop'],
        'cgroup_parent': cattrs['HostConfig']['CgroupParent'],
        'container_name': cattrs['Name'][1:],
        'devices': [],
        'dns': cattrs['HostConfig']['Dns'],
        'dns_search': cattrs['HostConfig']['DnsSearch'],
        'environment': cattrs['Config']['Env'],
        'extra_hosts': cattrs['HostConfig']['ExtraHosts'],
        'image': cattrs['Config']['Image'],
        'labels': cattrs['Config']['Labels'],
        'links': cattrs['HostConfig']['Links'],
        #'log_driver': cattrs['HostConfig']['LogConfig']['Type'],
        #'log_opt': cattrs['HostConfig']['LogConfig']['Config'],
        'logging': {'driver': cattrs['HostConfig']['LogConfig']['Type'], 'options': cattrs['HostConfig']['LogConfig']['Config']},
        'networks': {x for x in cattrs['NetworkSettings']['Networks'].keys() if x != 'bridge'},
        'security_opt': cattrs['HostConfig']['SecurityOpt'],
        'ulimits': cattrs['HostConfig']['Ulimits'],
        'volumes': cattrs['HostConfig']['Binds'],
        'volume_driver': cattrs['HostConfig']['VolumeDriver'],
        'volumes_from': cattrs['HostConfig']['VolumesFrom'],
        'entrypoint': cattrs['Config']['Entrypoint'],
        'user': cattrs['Config']['User'],
        'working_dir': cattrs['Config']['WorkingDir'],
        'domainname': cattrs['Config']['Domainname'],
        'hostname': cattrs['Config']['Hostname'],
        'ipc': cattrs['HostConfig']['IpcMode'],
        'mac_address': cattrs['NetworkSettings']['MacAddress'],
        'privileged': cattrs['HostConfig']['Privileged'],
        'restart': cattrs['HostConfig']['RestartPolicy']['Name'],
        'read_only': cattrs['HostConfig']['ReadonlyRootfs'],
        'stdin_open': cattrs['Config']['OpenStdin'],
        'tty': cattrs['Config']['Tty']
    }

    # Populate devices key if device values are present
    if cattrs['HostConfig']['Devices']:
        values['devices'] = [x['PathOnHost']+':'+x['PathInContainer'] for x in cattrs['HostConfig']['Devices']]
    
    networks = {}
    if values['networks'] == set():
        del values['networks']
    else:
        networklist = c.networks.list()
        for network in networklist:
            if network.attrs['Name'] in values['networks']:
                networks[network.attrs['Name']] = {'external': (not network.attrs['Internal'])}

    # Check for command and add it if present.
    if cattrs['Config']['Cmd'] != None:
        values['command'] = " ".join(cattrs['Config']['Cmd']),

    # Check for exposed/bound ports and add them if needed.
    try:
        expose_value =  list(cattrs['Config']['ExposedPorts'].keys())
        ports_value = [cattrs['HostConfig']['PortBindings'][key][0]['HostIp']+':'+cattrs['HostConfig']['PortBindings'][key][0]['HostPort']+':'+key for key in cattrs['HostConfig']['PortBindings']]

        # If bound ports found, don't use the 'expose' value.
        if (ports_value != None) and (ports_value != "") and (ports_value != []) and (ports_value != 'null') and (ports_value != {}) and (ports_value != "default") and (ports_value != 0) and (ports_value != ",") and (ports_value != "no"):
            for index, port in enumerate(ports_value):
                if port[0] == ':':
                    ports_value[index] = port[1:]

            values['ports'] = ports_value
        else:
            values['expose'] = expose_value

    except (KeyError, TypeError):
        # No ports exposed/bound. Continue without them.
        ports = None

    # Iterate through values to finish building yaml dict.
    for key in values:
        value = values[key]
        if (value != None) and (value != "") and (value != []) and (value != 'null') and (value != {}) and (value != "default") and (value != 0) and (value != ",") and (value != "no"):
            ct[key] = value

    return cfile, networks

def Convert(lst):
    res_dct = {lst[i]: lst[i + 1] for i in range(0, len(lst), 2)}
    return res_dct



logger.info("Configuring app")
app = FastAPI(title="DeCompose", description="Generate docker-compose from running containers", version="1.0.0",
              docs_url=None, redoc_url=None)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:;"
        )
        return response

app.add_middleware(SecurityHeadersMiddleware)

app.mount("/dist", StaticFiles(directory="dist"), name="dist")
app.mount("/js", StaticFiles(directory="dist/js"), name="js")
app.mount("/css", StaticFiles(directory="dist/css"), name="css")
templates = Jinja2Templates(directory="templates/")


@app.get("/api/containers")
def get_containers(request: Request):
    cnames = []
    client = docker.from_env()
    containers = client.containers.list(all=True)
    for c in containers:
        cnames.append(c.name)
    c_names = tuple(cnames)
    return JSONResponse(c_names)

@app.get("/api/generate")
def generate_compose(request: Request, cname: str=""):
    validate_cname(cname)
    data = main(cname)
    return pyaml.dump(data)

@app.get("/api/download")
def get_compose(request: Request, cname: str=""):
    import tempfile
    validate_cname(cname)
    data = main(cname)
    safe_name = os.path.basename(cname)
    filename = f"{safe_name}-docker-compose.yaml"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        pyaml.dump(data, tmp)
        tmp_path = tmp.name
    return FileResponse(tmp_path, media_type='application/octet-stream', filename=filename)

@app.get("/")
def home(request: Request):
    logger.info("loading default page")
    return templates.TemplateResponse('index.html', context={'request': request})


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8080)
