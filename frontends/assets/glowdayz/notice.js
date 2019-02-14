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

function NoticeManager(getWrapper, getLimitPerPage){
    var wrapper = getWrapper;
    var limitPerPage = getLimitPerPage;

    var listWrapper = wrapper.getElementsByClassName('list')[0];
    var listHtmlWrapper = document.createElement('ul');
    var moreBtn = wrapper.getElementsByClassName('moreView-btn')[0];
    var listHtml = '';
    var params = {
        limit: limitPerPage
    };
    var data;

    var nextPage;
    var totalCount;

    function ajax(getParams, getSts){
        $.ajax({
            url: '/api/v2/notices',
            type: 'GET',
            data: getParams,
            dataType: 'json',
            success: function(getData){
                data = getData;
                setList(getSts);
            },
            error: function(request,status,error){
                // console.log("code:"+request.status+"\n"+"message:"+request.responseText+"\n"+"error:"+error);
                location.replace('/webview/error/');
            }
        });
    }
    ajax(params);
    // 공지사항리스트 'ajax' 요청

    moreBtn.getElementsByClassName('cover')[0].onclick = function(){
        if (nextPage === undefined) return;
        params.cursor = nextPage;
        ajax(params, 'more');
    };
    // '더보기' 버튼 클릭 시

    function setList(getSts){
        if (nextPage === undefined) nextPage = 1;

        var noticeArr = data.notices;
        var noticeArrLeng = noticeArr.length;
        if (data.total_count !== undefined) totalCount = data.total_count;

        if (listWrapper.getElementsByTagName('ul')[0]) {
            listWrapper.removeChild(listWrapper.getElementsByTagName('ul')[0]);
        }
        if (getLimitPerPage < totalCount) {

            wrapper.className = wrapper.className.replace('more', '');
            wrapper.className = wrapper.className + ' more';
            moreBtn.getElementsByClassName('present')[0].innerHTML = nextPage;
            var totalPage = Math.ceil(totalCount / limitPerPage);
            if ( totalPage === nextPage ) {
                wrapper.className = wrapper.className.replace('more', '');
            }
            moreBtn.getElementsByClassName('total')[0].innerHTML = totalPage;
        }

        var newdate;

        for (var i=0; i<noticeArrLeng; i++) {
            if (!noticeArr[i]) break;
            newdate = new Date(noticeArr[i].created_at);
            newdate = newdate.setCustomForm('-');

            listHtml += '' +
                '<li>' +
                '<a href="glowpick://glowpick.com?type=19&code=' + noticeArr[i].notice_id + '">' +
                '<h2>' + noticeArr[i].subject + '</h2>' +
                '<h3>' + newdate + '</h3>' +
                '<div class="icon"></div>' +
                '<div class="cover"></div>' +
                '</a>'+
                '</li>';
        }
        nextPage = data.paging.next;
        listHtmlWrapper.innerHTML = listHtml;
        listWrapper.appendChild(listHtmlWrapper);
    }
    // 'ajax'로 받은 공지사항 리스트를 뿌리기

    document.addEventListener('touchstart', function(event) {
        if(event.target.className !== 'cover') return false;
        if(event.target.parentNode.tagName !== 'A') return false;
        event.target.parentNode.style.background = 'f2f2f2';
    },false);
}

NoticeManager(document.getElementsByClassName('m-notice')[0], 20);