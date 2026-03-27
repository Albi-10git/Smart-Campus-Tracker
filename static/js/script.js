function showToast(message, type="info"){

let stack = document.getElementById("toast-stack")

if(!stack){
stack = document.createElement("div")
stack.id = "toast-stack"
stack.className = "toast-stack"
document.body.appendChild(stack)
}

let toast = document.createElement("div")
toast.className = `toast toast-${type}`
toast.innerHTML = `
<p class="toast-title">Notification</p>
<p class="toast-message">${message}</p>
`

stack.appendChild(toast)

setTimeout(()=>{
toast.remove()
if(!stack.children.length){
stack.remove()
}
},3000)

}


function registerStudent(){

fetch("/register_student",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({

name:document.getElementById("name").value,
register_number:document.getElementById("register").value,
rfid_tag:document.getElementById("rfid").value

})

})
.then(async res=>({
ok:res.ok,
data:await res.json()
}))
.then(data=>{
showToast(data.data.message,data.ok ? "success" : "error")

if(!data.ok){
return
}

document.getElementById("name").value=""
document.getElementById("register").value=""
document.getElementById("rfid").value=""
loadStudents(currentStudentSort)

})

}


let pendingStudentDelete = null
let currentStudentSort = "name"


function openStudentDrawer(){

const drawer = document.getElementById("student-drawer")

if(!drawer){
return
}

drawer.classList.remove("hidden")
drawer.classList.add("flex")
loadStudents(currentStudentSort)

}


function closeStudentDrawer(){

const drawer = document.getElementById("student-drawer")

if(!drawer){
return
}

drawer.classList.add("hidden")
drawer.classList.remove("flex")

}


function refreshStudents(){

loadStudents(currentStudentSort)

}


function updateStudentSortButtons(){

const nameButton = document.getElementById("student-sort-name")
const rfidButton = document.getElementById("student-sort-rfid")

if(nameButton){
nameButton.classList.toggle("student-filter-active", currentStudentSort === "name")
}

if(rfidButton){
rfidButton.classList.toggle("student-filter-active", currentStudentSort === "rfid")
}

}


function loadStudents(sortMode=currentStudentSort){

const studentList = document.getElementById("student-list")

if(!studentList){
return
}

currentStudentSort = sortMode
updateStudentSortButtons()

fetch(`/students?sort=${encodeURIComponent(currentStudentSort)}`)
.then(res=>res.json())
.then(data=>{

if(!data.length){
studentList.innerHTML = `
<div class="student-empty-state">
<p class="student-empty-title">No students registered yet</p>
<p class="helper-text">Students you add will appear here with their register number and RFID assignment.</p>
</div>
`
return
}

studentList.innerHTML = data.map(student=>`
<article class="student-card">
<div class="student-card-copy">
<div class="student-card-topline">
<p class="student-card-name">${student.name}</p>
<span class="student-chip">${student.register_number}</span>
</div>
<p class="student-card-meta">RFID: ${student.rfid_tag || "Not assigned yet"}</p>
</div>
<button class="btn btn-danger-soft student-delete-btn" onclick="openDeleteStudentModal('${student.id}','${escapeHtml(student.name)}')">Delete</button>
</article>
`).join("")

})

}


function openDeleteStudentModal(studentId, studentName){

const modal = document.getElementById("delete-student-modal")
const message = document.getElementById("delete-student-message")

if(!modal || !message){
return
}

pendingStudentDelete = studentId
message.textContent = `Delete ${studentName}? This will remove the student record and free the RFID for another student.`
modal.classList.remove("hidden")
modal.classList.add("flex")

}


function closeDeleteStudentModal(){

const modal = document.getElementById("delete-student-modal")

if(!modal){
return
}

pendingStudentDelete = null
modal.classList.add("hidden")
modal.classList.remove("flex")

}


function confirmDeleteStudent(){

if(!pendingStudentDelete){
return
}

fetch(`/delete_student/${pendingStudentDelete}`,{
method:"POST"
})
.then(async res=>({
ok:res.ok,
data:await res.json()
}))
.then(result=>{
showToast(result.data.message,result.ok ? "success" : "error")

if(!result.ok){
return
}

closeDeleteStudentModal()
loadStudents(currentStudentSort)
})

}


function escapeHtml(value){

return String(value)
.replaceAll("&","&amp;")
.replaceAll("<","&lt;")
.replaceAll(">","&gt;")
.replaceAll('"',"&quot;")
.replaceAll("'","&#39;")

}


function registerVisitor(){

fetch("/register_visitor",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({

name:document.getElementById("vname").value,
phone:document.getElementById("phone").value,
purpose:document.getElementById("purpose").value,
rfid_tag:document.getElementById("vrfid").value

})

})
.then(res=>res.json())
.then(data=>{
showToast(data.message,"success")

document.getElementById("vname").value=""
document.getElementById("phone").value=""
document.getElementById("purpose").value=""
document.getElementById("vrfid").value=""

})

}


function scanRfid(){

const rfidTagInput = document.getElementById("scanner-rfid-tag")
const locationSelect = document.getElementById("scanner-location")
const customLocationInput = document.getElementById("custom-location")
const rfidTag = rfidTagInput ? rfidTagInput.value.trim() : ""
let selectedLocation = locationSelect ? locationSelect.value : "Main Gate"
const customLocation = customLocationInput ? customLocationInput.value.trim() : ""

if(!rfidTag){
alert("Please enter RFID tag")
return
}

if(selectedLocation === "Custom" && !customLocation){
alert("Please enter custom location")
return
}

if(selectedLocation === "Custom"){
selectedLocation = saveCustomLocation(customLocation)
}

const location = selectedLocation

fetch("/rfid_scan",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({

rfid_tag:rfidTag,
location:location

})

})
.then(res=>res.json())
.then(data=>{
showToast(data.message,"info")

if(rfidTagInput){
rfidTagInput.value=""
}

if(customLocationInput){
customLocationInput.value=""
}

toggleCustomLocation()
loadLogs()
})

}


function toggleCustomLocation(){

const locationSelect = document.getElementById("scanner-location")
const customLocationWrap = document.getElementById("custom-location-wrap")

if(!locationSelect || !customLocationWrap){
return
}

if(locationSelect.value === "Custom"){
customLocationWrap.classList.remove("hidden")
customLocationWrap.classList.add("flex")
}else{
customLocationWrap.classList.add("hidden")
customLocationWrap.classList.remove("flex")
}

}


function saveCustomLocation(customLocation){

const locationSelect = document.getElementById("scanner-location")
const customLocationInput = document.getElementById("custom-location")

if(!locationSelect){
return customLocation
}

const normalizedLocation = customLocation.trim()
const existingOption = Array.from(locationSelect.options).find(option=>
option.value.toLowerCase() === normalizedLocation.toLowerCase()
)

if(existingOption){
locationSelect.value = existingOption.value
}else{
const customOption = document.createElement("option")
customOption.value = normalizedLocation
customOption.textContent = normalizedLocation

const customTriggerOption = Array.from(locationSelect.options).find(option=>option.value === "Custom")

if(customTriggerOption){
locationSelect.insertBefore(customOption, customTriggerOption)
}else{
locationSelect.appendChild(customOption)
}

locationSelect.value = normalizedLocation
showToast(`Location "${normalizedLocation}" added successfully`,"success")
}

if(customLocationInput){
customLocationInput.value = ""
}

toggleCustomLocation()
return locationSelect.value

}


function isRecentLog(timestamp){

if(!timestamp){
return true
}

const parsedTimestamp = new Date(timestamp)

if(Number.isNaN(parsedTimestamp.getTime())){
return true
}

const oneDayInMilliseconds = 24 * 60 * 60 * 1000
return Date.now() - parsedTimestamp.getTime() <= oneDayInMilliseconds

}


function loadLogs(){

fetch("/logs")
.then(res=>res.json())
.then(data=>{

let table = document.getElementById("logs")

table.innerHTML=""

data.forEach(log=>{

const timeIn = log.time_in || log.timestamp || ""
const timeOut = log.time_out || "-"

if(!isRecentLog(timeIn)){
return
}

let row = `
<tr>
<td>${log.name}</td>
<td>${log.register_number || "-"}</td>
<td>${log.location}</td>
<td>${timeIn || "-"}</td>
<td>${timeOut}</td>
</tr>
`

table.innerHTML += row

})

})

}


function clearLogs(){

openClearLogsModal()

}


function openClearLogsModal(){

const modal = document.getElementById("clear-logs-modal")

if(!modal){
return
}

modal.classList.remove("hidden")
modal.classList.add("flex")

}


function closeClearLogsModal(){

const modal = document.getElementById("clear-logs-modal")

if(!modal){
return
}

modal.classList.add("hidden")
modal.classList.remove("flex")

}


function confirmClearLogs(){

fetch("/clear_logs",{
method:"POST"
})
.then(res=>res.json())
.then(data=>{
closeClearLogsModal()
showToast(data.message,"success")

const table = document.getElementById("logs")

if(table){
table.innerHTML = ""
}
})

}


document.addEventListener("DOMContentLoaded",()=>{
const locationSelect = document.getElementById("scanner-location")
const clearLogsModal = document.getElementById("clear-logs-modal")
const deleteStudentModal = document.getElementById("delete-student-modal")

if(locationSelect){
locationSelect.addEventListener("change",toggleCustomLocation)
toggleCustomLocation()
}

if(clearLogsModal){
clearLogsModal.addEventListener("click",(event)=>{
if(event.target === clearLogsModal){
closeClearLogsModal()
}
})
}

if(deleteStudentModal){
deleteStudentModal.addEventListener("click",(event)=>{
if(event.target === deleteStudentModal){
closeDeleteStudentModal()
}
})
}

if(document.getElementById("logs")){
loadLogs()
}

})
