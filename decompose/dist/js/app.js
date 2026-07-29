ace.config.set("basePath", "js");

$(document).ready(function () {

    $.get("api/containers", function (data) {
        fillContainersList(data);
    });

    $('#generate').click(function () {
        var cname = $('#containers').val();
        $.get("api/generate?cname=" + encodeURIComponent(cname), function (data) {
            $('#editor').ace({ theme: 'twilight', lang: 'yaml' });
            var editor = $('#editor').data('ace').editor.ace;
            editor.session.setValue(data);
        });
    });

    $('#download').click(function () {
        var cname = $('#containers').val();
        window.location.href = "api/download?cname=" + encodeURIComponent(cname);
    });

});

function fillContainersList(data) {
    var select = document.getElementById('containers');
    for (var i = 0; i < data.length; i++) {
        // Use new Option() so the name is assigned as text (textContent),
        // never parsed as HTML — avoids a DOM-based XSS sink.
        select.appendChild(new Option(data[i], data[i]));
    }
    $('#containers').select2();
}
