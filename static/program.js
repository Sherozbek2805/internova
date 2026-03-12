async function loadInternships() {

const res = await fetch("/api/internships")

const internships = await res.json()

const table = document.getElementById("manageInternshipsBody")

if(!table) return

table.innerHTML = ""

internships.forEach(i => {

table.innerHTML += `
<tr class="border-b border-white/5 hover:bg-white/10">

<td class="py-4 font-semibold text-white">
${i.title}
</td>

<td>
<span class="text-green-400 text-xs">Active</span>
</td>

<td class="text-gray-300">
0
</td>

<td class="text-gray-300">
${i.deadline}
</td>

<td class="text-right">
<a href="/applicants"
class="px-3 py-1 text-xs bg-blue-500 rounded">
View
</a>
</td>

</tr>
`
})

}


async function postInternship() {

const title = document.getElementById("title").value
const company = document.getElementById("company").value
const deadline = document.getElementById("deadline").value

await fetch("/api/internships", {

method: "POST",

headers: {
"Content-Type": "application/json"
},

body: JSON.stringify({
title,
company,
deadline
})

})

alert("Internship posted!")

}


document.addEventListener("DOMContentLoaded", () => {

loadInternships()

})