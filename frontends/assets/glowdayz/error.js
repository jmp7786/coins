var doc = document;

document.querySelector('.toRefresh').onclick = function(){
    location.reload();
};
document.querySelector('.toHome').onclick = function(){
    location.replace('glowpick://glowpick.com?type=24&code=');
};