
function toggleTheme(){const h=document.documentElement;h.dataset.theme=h.dataset.theme==='light'?'dark':'light';localStorage.setItem('assetvault-theme',h.dataset.theme)}
(function(){const t=localStorage.getItem('assetvault-theme');if(t)document.documentElement.dataset.theme=t})();
function showToast(msg){let t=document.getElementById('toast');if(!t){t=document.createElement('div');t.id='toast';t.className='toast';document.body.appendChild(t)}t.textContent=msg;t.style.display='block';setTimeout(()=>t.style.display='none',2200)}
function copyText(text){if(!text){showToast('No public link. Enable public sharing first.');return;}navigator.clipboard.writeText(text).then(()=>showToast('Direct file link copied')).catch(()=>{prompt('Copy this link:',text)})}
function bindFilePicker(){const input=document.getElementById('assetFile'), out=document.getElementById('selectedFile');if(!input||!out)return;input.addEventListener('change',()=>{if(!input.files.length){out.textContent='No file selected';return}const f=input.files[0];out.textContent='Selected: '+f.name+' • '+(f.size/1024/1024).toFixed(2)+' MB';});}
document.addEventListener('DOMContentLoaded',bindFilePicker);
