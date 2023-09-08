function hideItem(id) {
  const element = document.getElementById(id).parentElement;
  //console.log('Classes before ' + element.classList);
  element.classList.remove("showItem"); // Remove showItem
  element.classList.add("hideItem"); // Add showItem
  //console.log('Classes after ' + element.classList);
}

function showItem(id) {
  const element = document.getElementById(id).parentElement;
  //console.log('Classes before ' + element.classList);
  element.classList.remove("hideItem"); // Remove hideItem
  element.classList.add("showItem"); // Add showItem
  //console.log('Classes after ' + element.classList);
}

function resultCheck(element) {
  //console.log('Run resultCheck');
  //console.log(element.id);
  formNum = element.id.replace("id_form-", "").replace("-result", "");
  //console.log('Form number is ' + formNum);
  opt = 0;
  for (let k = 0; k < element.length; k++) {
    //console.log("Opt " + k + " " + element[k].value + element[k].selected);
    if (element[k].selected) {
      opt = k;
      break;
    }
  }
  //console.log("Opt selected " + opt);
  // get the right spread element
  sId = "id_form-" + formNum + "-spread";
  //console.log("Spread id " + sId);
  //oSpread = document.getElementById(sId);
  if (opt == 3) {
    hideItem(sId);
  }
  else {
    showItem(sId);
  }
}

function deleteme(element) {
  const treatmentLines = document.getElementsByClassName("formResult");

  var children
  var rowNum, temp, opt
  for (let i = 0; i < treatmentLines.length; i++) {
    //treatmentLines[i].style.display = lDisp;
    //console.log(treatmentLines[i].innerHTML);
    children = treatmentLines[i].children;
    for (let j = 0; j < children.length; j++) {
      //console.log(children[j].id);
      temp = children[j].id;
      temp = temp.replace("id_form-", "").replace("-result", "");
      console.log(temp);
      opt = 0;
      for (let k = 0; k < children[j].length; k++) {
        console.log("Opt " + k + " " + children[j][k].value + children[j][k].selected);
        if (children[j][k].selected) {
          opt = k;
          break;
        }
      }
      oSpread = document.getElementById("id_form-" + temp + "-spread");
      console.log("Opt selected " + opt);
      if (opt == 0) {
        oSpread.style.display = "none";
      } else {
        oSpread.style.display = "inline";
      }
      //children[j].style.display = lDisp;
    }
  }
}