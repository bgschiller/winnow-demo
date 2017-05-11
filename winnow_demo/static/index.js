Array.from(document.querySelectorAll('input[name="predefined"][type="radio"]'))
    .forEach(function(inp){
        inp
        .addEventListener('click', function(evt){
            var textarea = document.querySelector('textarea[name="filter-json-input"]'),
                filt = evt.target.getAttribute('data-filter');
            textarea.value = JSON.stringify(JSON.parse(filt), null, 4);
        });
    });

var textarea = document.querySelector('textarea[name="filter-json-input"]');

function focusBuildMyOwn(){
    document.querySelector('input[type="radio"][name="predefined"][value="build-my-own"]').checked = true;
}
textarea.addEventListener('change', focusBuildMyOwn);
textarea.addEventListener('keyup', focusBuildMyOwn);
