function submitform(colID)
{
  colField = document.getElementById("id_colID");
  colField.value = colID;

  document.selectForm.submit();
}

function hideItem(id)
{
  const element = document.getElementById(id)
  element.classList.remove("showItem"); // Remove showItem
  element.classList.add("hideItem"); // Add showItem
}

function showItem(id)
{
  const element = document.getElementById(id)
  element.classList.remove("hideItem"); // Remove hideItem
  element.classList.add("showItem"); // Add showItem
}