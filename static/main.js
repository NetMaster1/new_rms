const plusButton = document.querySelector('#btn_id');
const form_id = document.querySelector('.form_id');
// const searchButton = document.querySelector('#btn_id');
// const ul = document.querySelector('#ul_id');
const row_id = document.querySelector('#identifier');
const wrapper = document.querySelector('#wrapper');
// const button=documennt.getElementById('btn-id')

// plusButton.addEventListener('click', createNewLine);
// searchButton.addEventListener('click', findValue);
plusButton.addEventListener('click', createNewLine);

function createNewLine()
{
    // e.preventDefault();

    console.log('Event listener works');
    console.log(row_id);
    const li = document.createElement('li.li_id');
    // li.textContent = 'Smth new'
    li.innerHTML = `<div class="row m-1"><div class="col-3"><input type="text" class="form-control" id="name" name="name" maxlength="50" value={{product.name}}></div><div class="col-2"><input type="number" class="form-control" id="quantity_plus" name="quantity_plus" maxlength="50" required></div><div class="col-2"><input type="number" class="form-control" id="price" name="price" maxlength="50" required></div><div class="col-2"><a href="#"><input type="" value="+" class="btn btn-info" id="btn-id"></a></div></div>`
           
    document.querySelector('ul.ul_id').appendChild(li);
   

    setTimeout(function () {
        $('message').fadeOut('slow');
    }3000);
    
    

}