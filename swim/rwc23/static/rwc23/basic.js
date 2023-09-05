function submitform(colID)
{
  colField = document.getElementById("id_colID");
  colField.value = colID;

  document.selectForm.submit();
}

