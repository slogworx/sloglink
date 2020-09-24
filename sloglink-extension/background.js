var currentTab;
var currentURL;
var shortLink

/*
 * Updates browserAction icon to indicate if a slog.link exists or not 
 */
function updateIcon(slogLink=false) {
  browser.browserAction.setIcon({
    path: slogLink ? {
      48: "icons/slog-32.png"
    } : {
      48: "icons/no-slog-32.png"
    },
    tabId: currentTab.id
  });
  browser.browserAction.setTitle({
    // Screen readers can see the title
    title: slogLink ? `${shortLink} (click to copy)` : 'No slog.link (click to create)!',
    tabId: currentTab.id
  }); 
}


async function postData(url = '', data = {}) {
  const response = await fetch(url, {
    method: 'POST', 
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: data
  });

  if(response.status === 500) {
    return '';
  } else {
    return response.text();
  }
}


/*
 * Switches currentTab to the active tab
 */
function updateActiveTab(tabs) {

  function updateTab(tabs) {
    if (tabs[0]) {
      currentTab = tabs[0];
      currentURL = currentTab.url
      console.log(`currentURL: ${currentURL}`)

      postData('https://slog.link/translate_link', `long_link=${currentURL}`)
      .then(data => {
        if(data) {
          shortLink = `https://slog.link/${data}`;
          updateIcon(true)
        } else {
            shortLink = '';
            updateIcon(false)
        }
        console.log(`getShortLink(): ${shortLink}`);
      });
    }
  }

  var gettingActiveTab = browser.tabs.query({active: true, currentWindow: true});
  gettingActiveTab.then(updateTab);
}


function copyShortLink() {
  if(shortLink) {
      navigator.clipboard.writeText(shortLink);
      console.log(`Wrote ${shortLink} to clipboard.`);
  } else {
    postData('https://slog.link/add_link', `new_link=${currentURL}`).then(updateIcon(true)).then(updateActiveTab);
    console.log(`Submitted request for slog.link: ${currentURL}`);
  }
}


browser.browserAction.onClicked.addListener(copyShortLink);

// listen to tab URL changes
browser.tabs.onUpdated.addListener(updateActiveTab);

// listen to tab switching
browser.tabs.onActivated.addListener(updateActiveTab);

// listen for window switching
browser.windows.onFocusChanged.addListener(updateActiveTab);

// update when the extension loads initially
updateActiveTab();