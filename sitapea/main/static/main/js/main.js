$('.mode-selector button').click(function() {
    pinpad_show(this);
});

$('#hide-pinpad-button').click(function() {
    pinpad_hide();
});

$('.PINbutton.clear').click(function() {
    pincode_clear();
    pinpad_timeout();
});


$('.PINbutton.number').click(function() {
    var pincode = $('#PINcode');
    if (pincode.val().length < pincode.attr('maxlength')) {
        pincode.val(pincode.val() + this.value);
    }
    pinpad_timeout();
});

$('.PINbutton.enter').click(function() {
    var pincode = $('#PINcode');
    var pinform = $('#PINform');
    if (pincode.val() && pinform.data('action')) {
        pinpad_hide();
        console.log(pinform.data('action'));
        console.log(pincode.val());

        var url = '/checkin/' + pincode.val()
                + '/' + pinform.data('action') + '/';

        $.post(
            url,
            '',
            function(result) {
                console.log(result);
                show_notification(result);
            }

        )
        .fail(function(result) {
            console.log(result)
        });

    };

});

function pincode_clear() {
    $('#PINcode').val('');
}

function pinpad_show(button) {
    pinpad_hide();
    var pinform = $('#PINform');
    pinform.data('action', button.id);
    $('.mode-selector-buttons .button button').removeClass('selected');
    $(button).addClass('selected');
    pincode_clear();
    pinform.animate({
        top: "50%",
    }, 250, function() {
        // Animation complete.
    });
    pinpad_timeout();
}

function pinpad_hide() {
    $('.mode-selector-buttons .button button').removeClass('selected');
    $('#PINform').animate({
        top: "-50%",
    }, 250, function() {
        // Animation complete.
    })
}

var pinpad_timer;
function pinpad_timeout() {
    clearTimeout(pinpad_timer);
    pinpad_timer = setTimeout(pinpad_hide, 30*1000);
}

var notification_timer;
function show_notification(result) {
    clearTimeout(notification_timer);
    var footer = $('#footer');
    var result_div = footer.find('.result');
    var checkin_result = '';
    result_div.attr('class', 'result');
    if (result['error'] == 'employee_does_not_exist') {
        checkin_result = 'Неправильный код сотрудника';
        result_div.addClass('error');
    }

    if (result['employee_name'] && result ['employee_surname']) {
        if (result['action'] == 'arrival') {
            checkin_result = result['employee_name'] + ' ' + result['employee_surname'] + ', добро пожаловать!'
        }
        if (result['action'] == 'leaving') {
            checkin_result = 'До свидания, ' + result['employee_name'] + ' ' + result['employee_surname'] + '!'
        }
    }

    result_div.html(checkin_result);
    footer.css('bottom', '-120px');
    footer.animate({
        bottom: "0",
    }, 250, function() {
        // Animation complete.
    });
    notification_timer = setTimeout(function() {
        footer.animate({
        bottom: "-120px",
    }, 250, function() {
        // Animation complete.
    });
    }, 5000 );


}

function updateTime() {
    var currentTime = new Date();
    var hours = currentTime.getHours();
    var minutes = currentTime.getMinutes();
    if (minutes < 10){
    minutes = "0" + minutes;
    }
    var v = hours + ":" + minutes;
    setTimeout("updateTime()",1000);
    $('#clock').html(v);
}
updateTime();