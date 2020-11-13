/* Send request to the server to add liked message to database */
async function likeWarble(like,message_id) {
    const response = await axios.post(`/users/add_like/${message_id}`, 
      {
        userId: like.userId,
        messageId: like.messageId
      }
    );
    return response.data.like;
}

/* Send request to the server to remove liked message from database */
async function deleteLike(message_id){
    const response = await axios.delete(`/users/add_like/${message_id}`);
    return response.data;
}

/* Will toggle between like message and not*/
$("button.thumbup").on("click",async function(evt){
    evt.preventDefault();
    const id = $(this).data('id');
    const $arr = $(this).closest("form").siblings();
    const $userId = getID($arr[1].href);
    const $messId = getID($arr[0].href);
    $(this).toggleClass("btn-secondary btn-primary");
    if($(this).hasClass("btn-primary")){
        await likeWarble({$userId,$messId},$messId);
    } else {
        if(window.location.pathname === '/messages/liked'){
            $(this).closest('.list-group-item').remove()
        }
        await deleteLike($messId);
    }
});

/* Will create a new message in the modal window*/
$(document).ready(function() {
    $('#add_form').on('click',"#add_me", async function(evt) {
        evt.preventDefault();
        const msg = $('#AddNewModal').find('.form-control').val();
        const data = await axios.post(`/messages/new`, {text: msg});
        console.log(data)
        if (data.status == 201) {
            $('#AddNewModal').modal('hide');
            location.reload();
        }
    });
});

/* Function to get values for user/message ids */
function getID(arr){
    const str = arr.lastIndexOf('/')+1;
    const end = arr.length;
    return arr.slice(str,end);
}