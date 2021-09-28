function runProcess() {
  getSpreadsheetData();
  makeOurForm();
}

function getSpreadsheetData() {
  // This function gives you an array of objects modeling a worksheet's tabular data, where the first items — column headers — become the property names.
  var sheets = SpreadsheetApp.getActiveSpreadsheet().getSheets();
  var arrayOfArrays = sheets[sheets.length - 1].getDataRange().getValues();
  var headers = arrayOfArrays.shift();
  return arrayOfArrays.map(function (row) {
    return row.reduce(function (memo, value, index) {
      if (value) {
        memo[headers[index]] = value;
      }
      return memo;
    }, {});
  });
}

function makeOurForm() {
  var sheets = SpreadsheetApp.getActiveSpreadsheet().getSheets();
  var sheet_name = sheets[sheets.length - 1].getSheetName();
  var week_num = sheet_name.charAt(sheet_name.length - 1);
  var form = FormApp.create('Week ' + week_num + ': Boyz and jordan pickem [21-22]');
  
  //form.setDescription(".");
  
  form.addTextItem().setTitle('Name').setRequired(true);
  form.addTextItem().setTitle('Email').setRequired(true);
  
  getSpreadsheetData().forEach(function (row) {
    var item = form.addMultipleChoiceItem();
    if(row.wk_day == 'MON') {
      item.setTitle(row.away_team_name + ' (' + row.away_line + ') @ ' + row.home_team_name + ' [MNF]')
      .setChoices([
        item.createChoice(row.away_team_name),
        item.createChoice(row.home_team_name),
      ]).setRequired(true);
     } else if (row.wk_day == 'THU') {
       item.setTitle(row.away_team_name + ' (' + row.away_line + ') @ ' + row.home_team_name + ' [TNF]')
      .setChoices([
        item.createChoice(row.away_team_name),
        item.createChoice(row.home_team_name),
      ]).setRequired(true);
    } else {
      item.setTitle(row.away_team_name + ' (' + row.away_line + ') @ ' + row.home_team_name)
      .setChoices([
        item.createChoice(row.away_team_name),
        item.createChoice(row.home_team_name),
      ]).setRequired(true)
    }
  });
  
  form.addTextItem()
      .setTitle('ATS bonus').setRequired(true);
}
