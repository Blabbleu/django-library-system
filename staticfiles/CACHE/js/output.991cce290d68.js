document.getElementById('book-search').addEventListener('input',function(){let query=this.value;fetch(`/readers/query_books/?q=${query}`).then(response=>response.json()).then(data=>{let tableBody=document.getElementById('book-table-body');tableBody.innerHTML='';data.forEach(book=>{let thumbnail=book.thumbnail?`<img src="${book.thumbnail}" alt="Thumbnail" class="img-thumbnail" style="width: 100px; height: auto;">`:'';let actionButton=book.requested?`<button class="fluent-button" disabled>Requested</button>`:`<form method="post" class="request-form" style="display: inline;">
            <input type="hidden" name="book" value="${book.id}">
            <input type="hidden" name="borrower" value="">
            <button type="submit" class="fluent-button">Request Borrow</button>
          </form>`;let row=`<tr>
                    <td>${thumbnail}</td>
                    <td>${book.isbn}</td>
                    <td>${book.title}</td>
                    <td>${book.author}</td>
                    <td>${book.categories}</td>
                    <td>${book.publication_year}</td>
                    <td>${actionButton}</td>
                   </tr>`;tableBody.innerHTML+=row;});attachRequestFormSubmit();}).catch(error=>console.error('Error fetching books:',error));});function attachRequestFormSubmit(){document.querySelectorAll('.request-form').forEach(form=>{form.addEventListener('submit',function(event){event.preventDefault();let formData=new FormData(this);fetch(this.action,{method:'POST',body:formData,headers:{'X-CSRFToken':formData.get('csrfmiddlewaretoken')}}).then(response=>response.json()).then(data=>{if(data.success){this.querySelector('button').innerText='Requested';this.querySelector('button').disabled=true;}}).catch(error=>console.error('Error submitting request:',error));});});}
attachRequestFormSubmit();;