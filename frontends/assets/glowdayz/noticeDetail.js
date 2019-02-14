Date.prototype.setCustomForm = function (btwStr){
    function make00(num){
        num = (num<10) ? '0'+(num) : num;
        return num;
    }
    var newDate = new Date(this);
    btwStr = btwStr || '';
    var fullYear = newDate.getFullYear();
    var month = newDate.getMonth()+1;
    month = make00(month);
    var date = newDate.getDate();
    date = make00(date);
    var formed = fullYear + btwStr + month + btwStr + date;
    return formed;
};
// 날짜 데이터를 로컬시간에 맞추고 시간이나 분을 00표기로함
// btwStr = 날짜사이문자

function NoticeDetail(getWrapper){
    var wrapper = getWrapper;
    var data;
    var noticeId = location.search.split('=')[1];

    var h1 = wrapper.getElementsByTagName('h1')[0];
    var h2 = wrapper.getElementsByTagName('h2')[0];
    var article = wrapper.getElementsByTagName('article')[0];

    function setNoticeDetail(){

        var newdate = new Date(data.created_at);
        newdate = newdate.setCustomForm('-');


        h1.innerHTML = data.subject;
        h2.innerHTML = newdate;
        article.innerHTML = data.content;
    }

    $.ajax({
        url: '/api/v2/notices/' + noticeId,
        type: 'GET',
        dataType: 'json',
        success: function(getData){
            data = getData;
            setNoticeDetail();
        },
        error: function(){
            location.replace('/webview/error/');
        }
    });
}

NoticeDetail(document.getElementsByClassName('m-noticeDetail')[0]);