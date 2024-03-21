var currentUrl = "";

chrome.storage.sync.get(["hidden", "backendUrl"], (data) => {
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

        function findImagesInPage() {
            result = [];
            if (currentUrl.indexOf('/photo/') == -1) {
                images = document.querySelector('div[data-testid="cellInnerDiv"]').getElementsByTagName('img')
                for (var i = 0; i < images.length; i++) {
                    if (images[i].getAttribute("alt") == "Image") {
                        let url = images[i].src;
                        result.push(url.substring(28, url.indexOf('?format=')))

                    }
                }
            } else {
                images = document.querySelectorAll('li[role="listitem"]')
                for (var i = 0; i < images.length; i++) {

                    let imgHtmlEl = images[i].getElementsByTagName('img')[0];
                    if (imgHtmlEl.getAttribute("alt") == "Image") {
                        let url = imgHtmlEl.src;
                        result.push(url.substring(28, url.indexOf('?format=')))

                    }
                }
            }
            return result;
        }


        function performCallToServer() {
            console.log("starting search");
            let imagesInPage = findImagesInPage();
            if (imagesInPage.length == 0) {
                replaceContentWithText('No image found. Go to tweet');
                return;
            }
            let postBody = JSON.stringify(imagesInPage);

            let loadImages = new XMLHttpRequest()
            loadImages.onreadystatechange = function () {
                if (this.readyState == 4) {
                    if (this.status == 200) {
                        console.log('Success');
                        let response = JSON.parse(this.responseText)
                        setContentResult(response, imagesInPage)
                    }
                    else {
                        setAsFailure()
                    }
                }
            }

            loadImages.open("POST", "http://localhost:8000/contains", true);
            loadImages.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
            loadImages.send(postBody);
        }

        function replaceContentWithText(string) {
            let text = document.createTextNode(string)
            let textDiv = document.createElement("div")
            textDiv.replaceChildren(text)
            textDiv.style.paddingLeft = '10px'
            textDiv.style.color = 'rgb(255 255 255)'
            contentDiv.replaceChildren(textDiv)
        }

        function setAsFailure() {
            replaceContentWithText('Failed to get response from server')
        }

        function setContentResult(response, imagesInPage) {
            if (response.length == 0) {
                replaceContentWithText('No saved pictures found for ' + listToString(imagesInPage))
            } else {

                let listTag = document.createElement("ul")
                for (let foundPicture of response) {
                    let listElement = document.createElement("li")
                    listElement.textContent = foundPicture.name
                    listElement.title = foundPicture.path
                    listElement.style.color = 'rgb(255 255 255)'
                    listTag.appendChild(listElement)
                }


                contentDiv.replaceChildren(listTag)
            }
        }

        function listToString(imagesInPage) {
            let res = ''
            for (let i = 0; i < imagesInPage.length; i++) {
                res = res + imagesInPage[i] + ' ';
            }
            return res;
        }

        function create_centering_div() {
            let centeringDiv = document.createElement("div")
            centeringDiv.style.width = TOP_BAR_HEIGHT + 'px'
            centeringDiv.style.height = TOP_BAR_HEIGHT + 'px'
            centeringDiv.classList.add('frame');
            return centeringDiv
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

            let refreshIcon = document.createElement("img")
            refreshIcon.src = chrome.runtime.getURL('images/resources/reload_icon.png')
            refreshIcon.alt = "Refresh"
            refreshIcon.style.width = (TOP_BAR_HEIGHT - 15) + 'px'
            refreshIcon.style.height = (TOP_BAR_HEIGHT - 15) + 'px'
            refreshIcon.draggable = false
            refreshIcon.addEventListener("click", async () => { checkURLchange(true) });

            let titleText = document.createElement('h3')
            titleText.textContent = " Image finder"
            titleText.style.width = (TOTAL_WIDTH - TOP_BAR_HEIGHT) + 'px'
            titleText.style.display = 'inline-block'
            titleText.style.float = 'left'
            titleText.style.padding = '40px'
            titleText.style.color = 'rgb(255 255 255)'

            var centeringDiv = create_centering_div()
            var centeringDiv2 = create_centering_div()


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

            // centeringDiv.replaceChildren(closeIcon)
            // centeringDiv2.replaceChildren(refreshIcon)
            // topBarDiv.replaceChildren(centeringDiv2, titleText, centeringDiv)

            centeringDiv.replaceChildren(refreshIcon, titleText, closeIcon)
            topBarDiv.replaceChildren(centeringDiv)

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

        function checkURLchange(forceReload = false) {
            let newUrl = window.location.href;
            if (forceReload || (newUrl != currentUrl)) {
                console.log("url changed!");
                currentUrl = newUrl;
                setAsLoading()

                setTimeout(() => {
                    performCallToServer()
                }, 1);
            }
        }


        setTimeout(() => {
            checkURLchange()
        }, 2500);
    }
})


console.log('Log reached');