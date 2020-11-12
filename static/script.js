
async function likeWarble(like,message_id) {
    const response = await axios.post(`/users/add_like/${message_id}`, 
      {
        userId: like.userId,
        messageId: like.messageId
      }
    );
    return response.data.like;
}

async function deleteLike(message_id){
    const response = await axios.delete(`/users/add_like/${message_id}`);
    return response.data;
}


$("button").on("click",async function(evt){
    evt.preventDefault();
    const id = $(this).data('id');
    const $arr = $(this).closest("form").siblings();
    const $userId = getID($arr[1].href);
    const $messId = getID($arr[0].href);
    $(this).toggleClass("btn-secondary btn-primary");
    if($(this).hasClass("btn-secondary")){
        await likeWarble({$userId,$messId},$messId);
    } else {
        await deleteLike($messId);
    }

});

function getID(arr){
    const str = arr.lastIndexOf('/')+1;
    const end = arr.length;
    return arr.slice(str,end);
}
