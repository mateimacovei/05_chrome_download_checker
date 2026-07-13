var currentUrl = "";

chrome.storage.sync.get(["hidden"], (data) => {
    if (data.hidden != true) {
        var TOTAL_HEIGHT = 300
        var TOTAL_WIDTH = 200
        var TOP_BAR_HEIGHT = 50
        var PNG_BUTTON_CONTAINER_HEIGHT = window.location.href.indexOf("=png") == -1 ? 40 : 0

        //Creating Elements
        var parentDiv = document.createElement("div")
        parentDiv.id = "downloadedFinderExtensionRootDiv"
        parentDiv.classList.add('downloaded-finder-fixed');
        parentDiv.style.width = TOTAL_WIDTH + 'px'
        parentDiv.style.height = TOTAL_HEIGHT + 'px'


        var topBarDiv = create_top_bar()
        var contentDiv = document.createElement("div")
        contentDiv.style.width = TOTAL_WIDTH + 'px'
        contentDiv.style.height = (TOTAL_HEIGHT - TOP_BAR_HEIGHT - PNG_BUTTON_CONTAINER_HEIGHT) + 'px'
        contentDiv.classList.add('downloaded-finder-frame');
        if (PNG_BUTTON_CONTAINER_HEIGHT > 0) {
            parentDiv.replaceChildren(topBarDiv, contentDiv, create_png_button_container())
        } else {
            parentDiv.replaceChildren(topBarDiv, contentDiv)
        }


        chrome.storage.sync.get("color", ({ color }) => {
            parentDiv.style.backgroundColor = color;
        });

        let requestDownloadCheck = globalThis.downloadedFinderExtension.requestDownloadCheck;
        let navigateToUrl = globalThis.downloadedFinderExtension.navigateToUrl;
        let parseTwitterImageName = globalThis.downloadedFinderExtension.parseTwitterImageName;

        function performCallToServer() {
            console.log("starting search");
            let imageInPage = parseTwitterImageName(currentUrl);
            if (!imageInPage) {
                replaceContentWithText('No image found. Go to tweet')
                return;
            }

            requestDownloadCheck({
                method: "GET",
                path: "/contains",
                query: { name: imageInPage },
            }, (data) => {
                if (data === null) {
                    setAsFailure()
                    return;
                }
                console.log('Success');
                setContentResult(data, imageInPage)
            });
        }

        function replaceContentWithText(string) {
            let text = document.createTextNode(string)
            let textDiv = document.createElement("div")
            textDiv.replaceChildren(text)
            textDiv.style.paddingLeft = '10px'
            textDiv.style.paddingRight = '10px'
            textDiv.style.color = 'rgb(255 255 255)'
            textDiv.style.overflowWrap = 'anywhere'
            contentDiv.replaceChildren(textDiv)
        }

        function setAsFailure() {
            replaceContentWithText('Failed to get response from server')
        }

        function setContentResult(response, imageInPage) {
            if (response.length == 0) {
                replaceContentWithText('No saved pictures found for ' + imageInPage)
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

        function create_toolbar_div() {
            let toolbarDiv = document.createElement("div")
            toolbarDiv.style.width = TOTAL_WIDTH + 'px'
            toolbarDiv.style.height = TOP_BAR_HEIGHT + 'px'
            toolbarDiv.classList.add('downloaded-finder-toolbar');
            return toolbarDiv
        }

        function create_png_button_container() {
            let pngButtonContainer = document.createElement("div")
            pngButtonContainer.style.width = TOTAL_WIDTH + 'px'
            pngButtonContainer.style.height = PNG_BUTTON_CONTAINER_HEIGHT + 'px'
            pngButtonContainer.classList.add('downloaded-finder-png-button-container')

            let button = document.createElement('button')
            button.classList.add('downloaded-finder-png-button')
            button.textContent = "Go to png"
            button.addEventListener('click', async () => {
                var newUrl = window.location.href.replace('=jpg', '=png')
                navigateToUrl(newUrl)
            });

            pngButtonContainer.replaceChildren(button)
            return pngButtonContainer
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
            topBarDiv.classList.add('downloaded-finder-top-bar');

            let refreshIcon = document.createElement("img")
            refreshIcon.src = chrome.runtime.getURL('images/resources/reload_icon.png')
            refreshIcon.alt = "Refresh"
            refreshIcon.style.width = (TOP_BAR_HEIGHT - 15) + 'px'
            refreshIcon.style.height = (TOP_BAR_HEIGHT - 15) + 'px'
            refreshIcon.style.flex = '0 0 auto'
            refreshIcon.draggable = false
            refreshIcon.addEventListener("click", async () => { checkURLchange(true) });

            let titleText = document.createElement('h3')
            titleText.textContent = "Image finder"
            titleText.style.flex = '1 1 auto'
            titleText.style.margin = '0'
            titleText.style.padding = '0'
            titleText.style.color = 'rgb(255 255 255)'
            titleText.style.fontSize = '16px'
            titleText.style.lineHeight = '18px'
            titleText.style.textAlign = 'center'
            titleText.style.whiteSpace = 'nowrap'

            var toolbarDiv = create_toolbar_div()


            let closeIcon = document.createElement("img")
            closeIcon.src = chrome.runtime.getURL('images/resources/close_icon.png')
            closeIcon.alt = "Close"
            closeIcon.style.width = (TOP_BAR_HEIGHT - 15) + 'px'
            closeIcon.style.height = (TOP_BAR_HEIGHT - 15) + 'px'
            closeIcon.style.flex = '0 0 auto'
            closeIcon.draggable = false
            closeIcon.addEventListener("click", async () => {
                parentDiv.style.display = "none"
                let hidden = true
                chrome.storage.sync.set({ hidden });
            });

            toolbarDiv.replaceChildren(refreshIcon, titleText, closeIcon)
            topBarDiv.replaceChildren(toolbarDiv)

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


        checkURLchange();
    }
})


console.log('Log reached');
