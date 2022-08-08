// Checking page title
// if (document.title.indexOf("Google") != -1) {
//Creating Elements
var parentDiv = document.createElement("div")
parentDiv.id = "downloadedFinderExtensionRootDiv"
parentDiv.classList.add('fixed');


chrome.storage.sync.get("color", ({ color }) => {
    parentDiv.style.backgroundColor = color;
});

setAsLoading()



// var t = document.createTextNode("CLICK ME. Page: "+window.location.href);
// parentDiv.appendChild(t);
//Appending to DOM 
document.body.appendChild(parentDiv);
// }



function setAsLoading() {
    var imageElement = document.createElement("img") 
    imageElement.src=chrome.runtime.getURL('images/loading.gif')
    imageElement.alt="Loading"

    parentDiv.replaceChildren(imageElement)
}

console.log('Log reached');