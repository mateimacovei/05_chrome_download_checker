(function() {
    let downloadedFinderExtension = globalThis.downloadedFinderExtension || {};

    function requestDownloadCheck(request, callback) {
        chrome.runtime.sendMessage({
            type: "CHECK_DOWNLOADS",
            ...request,
        }, (response) => {
            if (chrome.runtime.lastError || !response || !response.ok) {
                callback(null)
                return;
            }
            callback(response.data)
        });
    }

    function navigateToUrl(newUrl) {
        chrome.runtime.sendMessage({ type: "NAVIGATE", newUrl: newUrl });
    }

    function parseTwitterImageName(imageUrl) {
        if (!imageUrl) {
            return "";
        }

        try {
            let pathParts = new URL(imageUrl).pathname.split('/');
            let imageName = pathParts[pathParts.length - 1] || "";
            let extensionStart = imageName.lastIndexOf('.');
            if (extensionStart != -1) {
                return imageName.slice(0, extensionStart);
            }
            return imageName;
        } catch (error) {
            return "";
        }
    }

    downloadedFinderExtension.requestDownloadCheck = requestDownloadCheck;
    downloadedFinderExtension.navigateToUrl = navigateToUrl;
    downloadedFinderExtension.parseTwitterImageName = parseTwitterImageName;
    globalThis.downloadedFinderExtension = downloadedFinderExtension;
})();
