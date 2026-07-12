var currentUrl = window.location.href

if (currentUrl.indexOf("=png") == -1) {


    var parentDiv = document.createElement("div")
    parentDiv.classList.add('fixed');
    parentDiv.style.width='auto'

    chrome.storage.sync.get("color", ({ color }) => {
        parentDiv.style.backgroundColor = color;
    });

    var button = document.createElement('button')
    button.classList.add('rectangle')

    button.innerHTML = "Go to png"



    document.body.appendChild(parentDiv);
    parentDiv.replaceChildren(button);



    button.addEventListener('click', async () => {
        var newUrl = window.location.href.replace('=jpg', '=png')
        chrome.runtime.sendMessage({ type: "NAVIGATE", newUrl: newUrl });
    });
}

