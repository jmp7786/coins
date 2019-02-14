function ProfileManager(profile_wrapper, postal_wrapper, listPerPage, listLimit){
    var doc = document;
    var userId = location.search.split('=')[1];
    var user_data;

    var saveBtn = profile_wrapper.querySelector('.save-btn');
    var profile_form = profile_wrapper.querySelector('form');
    var profile_inputForm = profile_form.querySelectorAll('.necessary-form');
    var toProfileInput = profile_wrapper.querySelectorAll('.toPostalCode');

    var daumapi_wrapper = doc.querySelector('.daumapi');

    $.ajax({
        url: '/api/v2/users/' + userId + '/profile',
        type: 'GET',
        dataType: 'json',
        success: function(data){
            user_data = data;
            for (var obj in user_data) {
                if (profile_wrapper.querySelector('[data-key="' + obj + '"]')) {
                    profile_wrapper.querySelector('[data-key="' + obj + '"]').value = user_data[obj];
                    if (obj === 'address' || obj === 'zip') {
                        profile_wrapper.querySelector('[data-key="' + obj + '"]').innerHTML = user_data[obj];
                    }
                }
            }
	        saveBtn.removeAttribute('disabled');
        },
        error: function(){
            location.replace('/webview/error/');
        }
    });
    // 초기 유저정보 불러오기

    function isEmpty (getValue, txt) {
        if (!getValue) {
            var middleTxt = '를';
            if (txt === '이름') middleTxt = '을';
            alert(txt + '' + middleTxt + ' 입력해주세요.');
            return false;
        }
        return true;
    }
    // 프로필 '저장' 버튼 클릭 시 유효성 체크

    saveBtn.onclick = function () {
        var profile_params = {};

        for (var obj in user_data) {
            if (profile_wrapper.querySelector('[data-key="' + obj + '"]')) {
                var inputElemValue;
                var inputElemTitle = profile_wrapper.querySelector('[data-key="' + obj + '"]').getAttribute('data-title');
                if (obj === 'address' || obj === 'zip') {
                    inputElemValue = profile_wrapper.querySelector('[data-key="' + obj + '"]').textContent;
                } else {
                    inputElemValue = profile_wrapper.querySelector('[data-key="' + obj + '"]').value;
                }

                if (!isEmpty(inputElemValue, inputElemTitle)) {
                    profile_wrapper.querySelector('[data-key="' + obj + '"]').focus();
                    return false;
                } else {
                    profile_params[obj] = inputElemValue;
                }
            }
        }

        $.ajax({
            url: '/api/v2/users/' + userId + '/profile',
            type: 'PUT',
            data: profile_params,
            dataType: 'json',
            success: function(){
                alert('성공적으로 저장되었습니다.');
                location.replace('glowpick://glowpick.com?type=11&code=');
            },
            error: function(){
                location.replace('/webview/error/');
            }
        });
    };
    // 프로필 '저장' 버튼 클릭 시 유저정보 저장

    for (var i=0; i<toProfileInput.length; i++) {
        toProfileInput[i].addEventListener('click', function(){
            document.body.className = document.body.className.replace('postalCode', '');
            document.body.className = document.body.className + ' postalCode';
            daumapi_fuc();
        });
    }
    postal_wrapper.querySelector('.close-btn').onclick = function(){
        document.body.className = document.body.className.replace('postalCode', '');
        daumapi_wrapper.style.display = 'none';
        postal_wrapper.className = 'm-postalCode';
    };
    // 프로필 화면 과 우편번호찾기 화면을 토글

    function daumapi_fuc() {
        new daum.Postcode({
            hideMapBtn: true,
            hideEngBtn: true,
            oncomplete: function(data) {

                var fullAddr = ''; // 최종 주소 변수
                var extraAddr = ''; // 조합형 주소 변수

                // 사용자가 선택한 주소 타입에 따라 해당 주소 값을 가져온다.
                if (data.userSelectedType === 'R') { // 사용자가 도로명 주소를 선택했을 경우
                    fullAddr = data.roadAddress;

                } else { // 사용자가 지번 주소를 선택했을 경우(J)
                    fullAddr = data.jibunAddress;
                }

                // 사용자가 선택한 주소가 도로명 타입일때 조합한다.
                if(data.userSelectedType === 'R'){
                    //법정동명이 있을 경우 추가한다.
                    if(data.bname !== ''){
                        extraAddr += data.bname;
                    }
                    // 건물명이 있을 경우 추가한다.
                    if(data.buildingName !== ''){
                        extraAddr += (extraAddr !== '' ? ', ' + data.buildingName : data.buildingName);
                    }
                    // 조합형주소의 유무에 따라 양쪽에 괄호를 추가하여 최종 주소를 만든다.
                    fullAddr += (extraAddr !== '' ? ' ('+ extraAddr +')' : '');
                }

                // 우편번호와 주소 정보를 해당 필드에 넣는다.
                document.querySelector('div.postalCode').innerHTML = data.zonecode;
                document.querySelector('div.address-input').innerHTML = fullAddr;
                document.querySelector('input.address_more').value = '';

                // iframe을 넣은 element를 안보이게 한다.
                // (autoClose:false 기능을 이용한다면, 아래 코드를 제거해야 화면에서 사라지지 않는다.)
                daumapi_wrapper.style.display = 'none';
                postal_wrapper.querySelector('.close-btn').click();
            },
            // 우편번호 찾기 화면 크기가 조정되었을때 실행할 코드를 작성하는 부분. iframe을 넣은 element의 높이값을 조정한다.
            onresize : function(size) {
                daumapi_wrapper.style.height = size.height+'px';
            },
            width : '100%',
            height : '100%'
        }).embed(daumapi_wrapper);

        // iframe을 넣은 element를 보이게 한다.
        daumapi_wrapper.style.display = 'block';
    }
    // 다음 우편번호 api
}

ProfileManager(document.getElementsByClassName('m-profile')[0], document.getElementsByClassName('m-postalCode')[0], 20, 100);