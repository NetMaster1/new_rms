// const plusButton = document.querySelector('#btn_id');

// plusButton.addEventListener('click', createNewLine);


// function createNewLine()
// {

//     console.log('Event listener works');
//     console.log(row_id);
//     const li = document.createElement('li.li_id');
//     // li.textContent = 'Smth new'
//     li.innerHTML = `<div class="row m-1"><div class="col-3"><input type="text" class="form-control" id="name" name="name" maxlength="50" value={{product.name}}></div><div class="col-2"><input type="number" class="form-control" id="quantity_plus" name="quantity_plus" maxlength="50" required></div><div class="col-2"><input type="number" class="form-control" id="price" name="price" maxlength="50" required></div><div class="col-2"><a href="#"><input type="" value="+" class="btn btn-info" id="btn-id"></a></div></div>`
           
//     document.querySelector('ul.ul_id').appendChild(li);

    const btn_modal =document.querySelector('.btn_modal')
    const enterModal =document.querySelector('.enterModal')
    const btn_close =document.querySelector('.btn_close')

    btn_modal.addEventListener('click', openModal)
    btn_close.addEventListener('click', closeModal)

    function openModal (){
        enterModal.classList.add('openModal')
    }

    function closeModal() {
            enterModal.classList.remove('openModal')
        }