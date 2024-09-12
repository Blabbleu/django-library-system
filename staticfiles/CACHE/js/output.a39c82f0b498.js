document.getElementById('reader-search').addEventListener('input',function(){let query=this.value;fetch(`/readers/query/?q=${query}`).then(response=>response.json()).then(data=>{let tableBody=document.getElementById('reader-table-body');tableBody.innerHTML='';data.forEach(reader=>{let row=`<tr>
                        <td>${reader.id}</td>
                        <td>${reader.user__username}</td>
                        <td>${reader.reader_type}</td>
                        <td>${reader.owed_money}</td>
                        <td>${reader.credit_score}</td>
                        <td><fluent-button appearance="accent" onclick="location.href='/readers/manage/0/'.replace(0, ${reader.id})">Manage</fluent-button></td>
                       </tr>`;tableBody.innerHTML+=row;});});});;