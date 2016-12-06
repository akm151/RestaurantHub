var bio={
 "name":"Aman Kumar",
 "role":"Back End Developer",
 "contacts":{
  "mobile":"9800052262",
  "email":"akm151@gmail.com",
  "location":"Mysore"
 },
 "Welcomemsg":" ",
 "skills":["C/C++/C# ", "Python ", ".NET/Flask MVC Framework ", "HTML/CSS/JAVASCRIPT/JQuery "],
 "pictureurl":"static/fry.jpg"
};
var education={
 "schools":[
 {
  "name":"Hem Sheela Model School",
  "city":"Durgapur",
  "degree":"SSE",
  "major":["Science"],
  "dates":2008
 },
 {
  "name":"Hem Sheela Model School",
  "city":"Durgapur",
  "degree":"AISSCE",
  "major":["Science"],
  "dates":2010
 },
 {
  "name":"Institute Of Engineering & Management College",
  "city":"Kolkata",
  "degree":"B Tech.",
  "major":["Electronic and Communication Engineering"],
  "dates":2015
 }
 ]
}
var work={
 
 "workemployer":"Infosys Ltd.",
 "worktitle":"System engineer",
 "workdate":"September,2015",
 "worklocation":"Mysore",
 "workdesc":"Working on Order Management System(OMS) of Infosys using Visual Basic as language and .NET as framework.The system handles all the projects and their whereabouts received by Infosys. "
}
var projects={
 "project":[{
  "title":"START ACT",
  "date":2015,
  "desc":"bla bla",
 },
 {
  "title":"Industrail sol",
  "date":2015,
  "desc":"bla bla",
 }
 ]
}
if(bio.length!=0)
 {
  var formattedname=HTMLheaderName.replace("%data%",bio.name);
  $("#header").append(formattedname);
  var formattedrole=HTMLheaderRole.replace("%data%",bio.role);
  $("#header").append(formattedrole);
  var mobile=HTMLmobile.replace("%data%",bio.contacts.mobile);
  $("#header").append(mobile);
  var email=HTMLemail.replace("%data%",bio.contacts.email);
  $("#header").append(email);
  var loc=HTMLlocation.replace("%data%",bio.contacts.location);
  $("#header").append(loc);
  var pic=HTMLbioPic.replace("%data%",bio.pictureurl);
  $("#header").append(pic);
  var welcomemsg=HTMLwelcomeMsg.replace("%data%",bio.Welcomemsg);
  $("#header").append(welcomemsg);
if(bio.skills.length!=0)
 {
   var skillst=HTMLskillsStart.replace("%data%");
   $("#header").append(skillst);
   
   for (i in bio.skills)
   {
    var sk=HTMLskills.replace("%data%",bio.skills[i]);
    $("#skills").append(sk);
   };
   
 };
};
function displaywork()
{
 if (work.length!=0)
 {
  $("#workExperience").append(HTMLworkStart);
  var employer=HTMLworkEmployer.replace("%data%",work.workemployer);
  var title=HTMLworkTitle.replace("%data%",work.worktitle);
  var emptitle=employer+title;
  $(".work-entry:last").append(emptitle);
  var dates=HTMLworkDates.replace("%data%",work.workdate);
  $(".work-entry:last").append(dates);
  //var loc=HTMLworkLocation.replace("%data%",work.worklocation);
  //$(".work-entry:last").append(loc);
  var desc=HTMLworkDescription.replace("%data%",work.workdesc);
  $(".work-entry:last").append(desc);

 }
}
displaywork();

//function displayproj()
//{
// for (p in projects.project)
// {
//  $("#projects").append(HTMLprojectStart);
//  var title=HTMLprojectTitle.replace("%data%",projects.project[p].title);
//  $(".project-entry:last").append(title);
//  var date=HTMLprojectDates.replace("%data%",projects.project[p].date);
//  $(".project-entry:last").append(date);
//  var desc=HTMLprojectDescription.replace("%data%",projects.project[p].desc);
//  $(".project-entry:last").append(desc);
// }
//}
//displayproj();