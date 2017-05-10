Array.from(document.querySelectorAll('input[name="predefined"][type="radio"]'))
    .forEach(function(inp){
        inp
        .addEventListener('click', function(evt){
            var textarea = document.querySelector('textarea[name="filter-json-input"]'),
                filt = evt.target.getAttribute('data-filter');
            textarea.value = JSON.stringify(JSON.parse(filt), null, '    ');
        });
    });
