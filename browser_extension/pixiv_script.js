// add filters for https://www.pixiv.net/en/users/*, twitter home, twitter bookmarks, 
// or add more specific , like pixiv/artworks/*, pixiv/manga/*

var currentUrl = "";

chrome.storage.sync.get(["hidden","backendUrl"], (data) => {
    if (data.hidden != true) {
        var TOTAL_HEIGHT = 300
        var TOTAL_WIDTH = 200
        var TOP_BAR_HEIGHT = 50

        // Checking page title
        // if (document.title.indexOf("Google") != -1) {
        //Creating Elements
        var parentDiv = document.createElement("div")
        parentDiv.id = "downloadedFinderExtensionRootDiv"
        parentDiv.classList.add('fixed');
        parentDiv.style.width = TOTAL_WIDTH + 'px'
        parentDiv.style.height = TOTAL_HEIGHT + 'px'


        var topBarDiv = create_top_bar()
        var contentDiv = document.createElement("div")
        contentDiv.style.width = TOTAL_WIDTH + 'px'
        contentDiv.style.height = (TOTAL_HEIGHT - TOP_BAR_HEIGHT) + 'px'
        contentDiv.classList.add('frame');
        parentDiv.replaceChildren(topBarDiv, contentDiv)


        chrome.storage.sync.get("color", ({ color }) => {
            parentDiv.style.backgroundColor = color;
        });

        // var previousUrl = '';
        // var observer = new MutationObserver(function (mutations) {
        //     if (location.href !== previousUrl) {
        //         previousUrl = location.href;
        //         console.log(`URL changed to ${location.href}`);
        //     }
        // });

        function performCallToServer(url) {
            let pictureSearch = url.split("/").at(-1)

            let loadImages = new XMLHttpRequest()
            loadImages.onreadystatechange = function () {
                if (this.readyState == 4) {
                    if (this.status == 200) {
                        console.log('Success');
                        let response = JSON.parse(this.responseText)
                        setContentResult(response, pictureSearch)
                    }
                    else {
                        setAsFailure()
                    }
                }
            }

            console.log('Seaching for ' + pictureSearch);

            loadImages.open("GET", "http://localhost:8000/contains?name=" + pictureSearch
                // + "?t=" + Math.random()
                , true);
            loadImages.send();
        }

        function replaceContentWithText(string) {
            let text = document.createTextNode(string)
            let textDiv = document.createElement("div")
            textDiv.replaceChildren(text)
            textDiv.style.paddingLeft = '10px'
            contentDiv.replaceChildren(textDiv)
        }

        function setAsFailure() {
            replaceContentWithText('Failed to get response from server')
        }

        function setContentResult(response, pictureSearch) {
            if (response.length == 0) {
                replaceContentWithText('No saved pictures found for ' + pictureSearch)
            } else {

                let listTag = document.createElement("ul")
                for (let foundPicture of response) {
                    let listElement = document.createElement("li")
                    listElement.textContent = foundPicture.name
                    listElement.title = foundPicture.path
                    listTag.appendChild(listElement)
                }


                contentDiv.replaceChildren(listTag)
            }
        }



        // var t = document.createTextNode("CLICK ME. Page: "+window.location.href);
        // parentDiv.appendChild(t);
        //Appending to DOM 
        document.body.appendChild(parentDiv);
        // }

        function create_top_bar() {
            let topBarDiv = document.createElement("div")
            topBarDiv.style.width = TOTAL_WIDTH + 'px'
            topBarDiv.style.height = TOP_BAR_HEIGHT + 'px'

            let titleText = document.createElement('h3')
            titleText.textContent = " Image finder"
            titleText.style.width = (TOTAL_WIDTH - TOP_BAR_HEIGHT) + 'px'
            titleText.style.display = 'inline-block'
            titleText.style.float = 'left'

            let centeringDiv = document.createElement("div")
            centeringDiv.style.width = TOP_BAR_HEIGHT + 'px'
            centeringDiv.style.height = TOP_BAR_HEIGHT + 'px'
            centeringDiv.classList.add('frame');

            let closeIcon = document.createElement("img")
            closeIcon.src = chrome.runtime.getURL('images/resources/close_icon.png')
            closeIcon.alt = "Close"
            closeIcon.style.width = (TOP_BAR_HEIGHT - 15) + 'px'
            closeIcon.style.height = (TOP_BAR_HEIGHT - 15) + 'px'

            closeIcon.draggable = false
            closeIcon.addEventListener("click", async () => {
                parentDiv.style.display = "none"
                let hidden = true
                chrome.storage.sync.set({ hidden });
            });

            centeringDiv.replaceChildren(closeIcon)
            topBarDiv.replaceChildren(titleText, centeringDiv)

            return topBarDiv
        }

        function setAsLoading() {
            var imageElement = document.createElement("img")
            imageElement.src = chrome.runtime.getURL('images/resources/loading.gif')
            imageElement.alt = "Loading"
            imageElement.style.width = "200px"
            imageElement.style.height = "200px"
            imageElement.draggable = false

            contentDiv.replaceChildren(imageElement)
        }

        function checkURLchange(){
            let newUrl = window.location.href;
            if(newUrl != currentUrl){
                console.log("url changed!");
                currentUrl = newUrl;
                setAsLoading()
                performCallToServer(currentUrl)
            }
        }
        
        checkURLchange()
    }
})


console.log('Log reached');