function hideItem(id) {
  const element = document.getElementById(id).parentElement;
  element.classList.remove("showItem");
  element.classList.add("hideItem");
}

function showItem(id) {
  const element = document.getElementById(id).parentElement;
  element.classList.remove("hideItem");
  element.classList.add("showItem");
}

function resultCheck(element) {
  const formNum = element.id.replace("id_form-", "").replace("-result", "");
  const drawValue = "3";
  const spreadId = "id_form-" + formNum + "-spread";

  if (element.value === drawValue) {
    hideItem(spreadId);
  } else {
    showItem(spreadId);
  }
}
