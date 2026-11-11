// Fix #3: WeakMap esterna per i timer, evita race condition su elementi DOM ricreati
const timers = new WeakMap();

// Fix #6: restringe checkTextBox ai soli INPUT di tipo testuale
function checkTextBox(el) {
  const textTypes = ['text', 'email', 'search', 'tel', 'url', 'password', ''];
  if (el.tagName === 'INPUT') {
    return textTypes.includes((el.type || '').toLowerCase());
  }
  return el.tagName === 'TEXTAREA' || el.contentEditable === 'true';
}

//get text from a text box
function getText(textBox) {
  if (textBox.contentEditable === 'true') {
    return textBox.textContent;
  } else {
    return textBox.value;
  }
}

//put new text in a text box
function giveBack(textBox, newText) {
  if (textBox.contentEditable === 'true') {
    textBox.textContent = newText;
  } else {
    textBox.value = newText;
  }
}

//ask background to hide personal info
function askBG(textBox) {
  //get what user typed
  var userText = getText(textBox);
  
  //skip if too short
  if (!userText || userText.length < 3) {
    return;
  }

  //ask background script for help
  chrome.runtime.sendMessage({
    action: 'hidePII',
    text: userText
  })
  .then(function(response) {
    if (response && response.success) {
      giveBack(textBox, response.hiddenText);
    }
  })
  .catch(function(error) {
    console.log('Error:', error);
  });
}

//user types something
function userIsTyping(event) {
  var textBox = event.target;
  
  // Fix #3: usa WeakMap invece di proprietà diretta sull'elemento DOM
  if (checkTextBox(textBox)) {
    clearTimeout(timers.get(textBox));
    timers.set(textBox, setTimeout(function() {
      askBG(textBox);
    }, 1000));
  }
}

//start watching for typing
document.addEventListener('input', userIsTyping);
