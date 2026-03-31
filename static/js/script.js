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
let pendingVisitorDelete = null
let currentStudentSort = "name"
let currentVisitorSort = "name"
let lastHardwareScanSignature = ""


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


function openVisitorDrawer(){

const drawer = document.getElementById("visitor-drawer")

if(!drawer){
return
}

drawer.classList.remove("hidden")
drawer.classList.add("flex")
loadVisitors(currentVisitorSort)

}


function closeVisitorDrawer(){

const drawer = document.getElementById("visitor-drawer")

if(!drawer){
return
}

drawer.classList.add("hidden")
drawer.classList.remove("flex")

}


function refreshVisitors(){

loadVisitors(currentVisitorSort)

}


function updateVisitorSortButtons(){

const nameButton = document.getElementById("visitor-sort-name")
const phoneButton = document.getElementById("visitor-sort-phone")
const rfidButton = document.getElementById("visitor-sort-rfid")

if(nameButton){
nameButton.classList.toggle("student-filter-active", currentVisitorSort === "name")
}

if(phoneButton){
phoneButton.classList.toggle("student-filter-active", currentVisitorSort === "phone")
}

if(rfidButton){
rfidButton.classList.toggle("student-filter-active", currentVisitorSort === "rfid")
}

}


function loadVisitors(sortMode=currentVisitorSort){

const visitorList = document.getElementById("visitor-list")

if(!visitorList){
return
}

currentVisitorSort = sortMode
updateVisitorSortButtons()

fetch(`/visitors?sort=${encodeURIComponent(currentVisitorSort)}`)
.then(res=>res.json())
.then(data=>{

if(!data.length){
visitorList.innerHTML = `
<div class="student-empty-state">
<p class="student-empty-title">No visitors registered yet</p>
<p class="helper-text">Visitors you add will appear here with their phone number, purpose, and RFID assignment.</p>
</div>
`
return
}

visitorList.innerHTML = data.map(visitor=>`
<article class="student-card">
<div class="student-card-copy">
<div class="student-card-topline">
<p class="student-card-name">${visitor.name}</p>
<span class="student-chip">${visitor.phone}</span>
</div>
<p class="student-card-meta">Purpose: ${escapeHtml(visitor.purpose || "Not provided")}</p>
<p class="student-card-meta">RFID: ${visitor.rfid_tag || "Not assigned yet"}</p>
</div>
<button class="btn btn-danger-soft student-delete-btn" onclick="openDeleteVisitorModal('${visitor.id}','${escapeHtml(visitor.name)}')">Delete</button>
</article>
`).join("")

})

}


function openDeleteVisitorModal(visitorId, visitorName){

const modal = document.getElementById("delete-visitor-modal")
const message = document.getElementById("delete-visitor-message")

if(!modal || !message){
return
}

pendingVisitorDelete = visitorId
message.textContent = `Delete ${visitorName}? This will remove the visitor record and free the RFID for another person.`
modal.classList.remove("hidden")
modal.classList.add("flex")

}


function closeDeleteVisitorModal(){

const modal = document.getElementById("delete-visitor-modal")

if(!modal){
return
}

pendingVisitorDelete = null
modal.classList.add("hidden")
modal.classList.remove("flex")

}


function confirmDeleteVisitor(){

if(!pendingVisitorDelete){
return
}

fetch(`/delete_visitor/${pendingVisitorDelete}`,{
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

closeDeleteVisitorModal()
loadVisitors(currentVisitorSort)
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

const phoneInput = document.getElementById("phone")
const phoneNumber = phoneInput ? phoneInput.value.replace(/\D/g,"").slice(0,10) : ""

if(phoneInput){
phoneInput.value = phoneNumber
}

fetch("/register_visitor",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({

name:document.getElementById("vname").value,
phone:phoneNumber,
purpose:document.getElementById("purpose").value,
rfid_tag:document.getElementById("vrfid").value

})

})
.then(async res=>({
ok:res.ok,
data:await res.json()
}))
.then(result=>{
const smsMessage = result.data.sms_message ? ` ${result.data.sms_message}` : ""
showToast(`${result.data.message}.${smsMessage}`.trim(),result.ok ? "success" : "error")

if(!result.ok){
return
}

document.getElementById("vname").value=""
document.getElementById("phone").value=""
document.getElementById("purpose").value=""
document.getElementById("vrfid").value=""

if(document.getElementById("visitor-list")){
loadVisitors(currentVisitorSort)
}

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
loadLatestLog()
})

}


function loadArduinoStatus(){

fetch("/arduino_status")
.then(res=>res.json())
.then(data=>{

const statusMessage = document.getElementById("arduino-status-message")
const lastScan = document.getElementById("arduino-last-scan")
const locationSelect = document.getElementById("scanner-location")

if(!statusMessage || !lastScan){
return
}

if(!data.enabled){
statusMessage.textContent = "Arduino bridge is disabled. Set ARDUINO_ENABLED=true to receive hardware scans."
lastScan.textContent = ""
return
}

if(!data.pyserial_installed){
statusMessage.textContent = "Arduino bridge is waiting for pyserial. Install it before starting hardware scans."
lastScan.textContent = ""
return
}

if(data.default_location && locationSelect && !locationSelect.dataset.readerInitialized){
const existingOption = Array.from(locationSelect.options).find(option=>
option.value.toLowerCase() === data.default_location.toLowerCase()
)

if(existingOption){
locationSelect.value = existingOption.value
}else{
const customOption = document.createElement("option")
customOption.value = data.default_location
customOption.textContent = data.default_location
locationSelect.insertBefore(customOption, locationSelect.lastElementChild)
locationSelect.value = data.default_location
}

locationSelect.dataset.readerInitialized = "true"
toggleCustomLocation()
}

if(data.connected){
statusMessage.textContent = `Arduino connected on ${data.port} at ${data.baud_rate} baud. Reader location: ${data.default_location}.`
}else if(data.last_error){
statusMessage.textContent = `Arduino not connected yet. ${data.last_error}`
}else{
statusMessage.textContent = `Waiting for Arduino reader on ${data.port}...`
}

if(data.last_scan_time){
const scanSignature = `${data.last_tag || ""}|${data.last_location || ""}|${data.last_scan_time}`
lastScan.textContent = `Last hardware scan: ${data.last_tag || "-"} at ${data.last_location || data.default_location} (${data.last_scan_time})${data.last_message ? ` - ${data.last_message}` : ""}`

if(scanSignature !== lastHardwareScanSignature){
lastHardwareScanSignature = scanSignature
loadLatestLog()
}
}else{
lastScan.textContent = "No hardware scans received yet."
}

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
renderLogs(data)

})

}


function loadLatestLog(){

fetch("/logs")
.then(res=>res.json())
.then(data=>{

const recentLogs = data.filter(log=>{
const timeIn = log.time_in || log.timestamp || ""
return isRecentLog(timeIn)
})

renderLogs(recentLogs.length ? [recentLogs[0]] : [])

})

}


function renderLogs(logs){

const table = document.getElementById("logs")

if(!table){
return
}

table.innerHTML = ""

logs.forEach(log=>{

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

closeClearLogsModal()

const table = document.getElementById("logs")

if(table){
table.innerHTML = ""
}

showToast("Dashboard logs cleared from view. Use Load Logs to show them again.","success")

}


document.addEventListener("DOMContentLoaded",()=>{
const locationSelect = document.getElementById("scanner-location")
const clearLogsModal = document.getElementById("clear-logs-modal")
const deleteStudentModal = document.getElementById("delete-student-modal")
const deleteVisitorModal = document.getElementById("delete-visitor-modal")
const phoneInput = document.getElementById("phone")

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

if(deleteVisitorModal){
deleteVisitorModal.addEventListener("click",(event)=>{
if(event.target === deleteVisitorModal){
closeDeleteVisitorModal()
}
})
}

if(phoneInput){
phoneInput.addEventListener("input",()=>{
phoneInput.value = phoneInput.value.replace(/\D/g,"").slice(0,10)
})
}

if(document.getElementById("arduino-status-panel")){
loadArduinoStatus()
setInterval(loadArduinoStatus,5000)
}

})
