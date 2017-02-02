var style = '<style>html, body{width: 100%;height: 100%;margin: 0px;padding: 0px;position: relative;} .centered-block {max-height: 50%;margin-left: auto;margin-right: auto;text-align: center;} .g-recaptcha div{margin-left: auto;margin-right: auto; text-align: center;} .img-responsive{max-width: 90%;height: 100%;} #timer{text-align: center;padding-bottom: 6px;} #messages{width: 180px;font-size: 14px;margin: 0 auto;padding: 4px;border: 1px solid grey;border-radius: 4px;background: ghostwhite;font-family: sans-serif;} .label{width: 140px;text-align: right;padding-right: 2px;display: inline-block;}</style>';
var statsElement = '<div id="messages"><div id="timer"></div><div id="status"></div><span class="label">Working accounts:</span><strong id="accounts_working">0</strong><br><span class="label">Remaining captchas:</span><strong id="accounts_captcha">0</strong><br><span class="label">Failed accounts:</span><strong id="accounts_failed">0</strong></div>';
var captchaOnly = '<div id="recaptcha"><div class="g-recaptcha" data-size="compact" data-sitekey="6LeeTScTAAAAADqvhqVMhPpr_vB9D364Ia-1dSgK" data-callback="captchaResponse"></div></div>';
var captchaPage = '<html>\n  <head>\n    <title>Pokémon GO</title>\n    <meta name="viewport" content="width=device-width, initial-scale=.9"/>\n     ' + style + '</head>\n  <body>\n    <div class="content">\n      <form action="?" method="POST">\n        ' + captchaOnly + '\n      </form>\n<br /><br />' + statsElement + '    </div>\n  </body>\n</html>';
var last_res = null;
var timer = {{timer}};

function initCaptchaPage(){
    document.body.parentElement.innerHTML = captchaPage;
    var script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jquery/3.1.0/jquery.min.js';
    script.type = 'text/javascript';
    document.getElementsByTagName('head')[0].appendChild(script);

    script = document.createElement('script');
    script.src = 'https://www.google.com/recaptcha/api.js';
    script.type = 'text/javascript';
    document.getElementById('recaptcha').appendChild(script);
    timer = {{timer}};
}

function refreshCaptcha() {
    var script = document.createElement('script');
    script.src = 'https://www.google.com/recaptcha/api.js';
    script.type = 'text/javascript';

    $('form').html(captchaOnly);
    $('#recaptcha').delay(500).append(script);
    refreshStats();
    $('#status').delay(1000).fadeOut(400);
}

function refreshStats() {
    $.getJSON('{{domain}}/get_stats', function(data){
        $('#accounts_working').text(data.working);
        $('#accounts_captcha').text(data.captcha);
        $('#accounts_failed').text(data.failed);
    });
}

var fnc = function(str){
    var elem = document.getElementById('g-recaptcha-response');
    var res  = elem ? (elem.value || str) : str;

    setTimeout(function(){
        if(res && last_res !== res){
            console.log(res);
            last_res = res;
            $.post('{{domain}}/submit_token', {token: res}, function(data) {
                if(data == "ok"){
                    $('#status').text('Captcha token submitted.');
                } else {
                    $('#status').text('Failed to submit captcha token.');
                }
                $('#status').fadeIn(200);
            });
            setTimeout(initCaptchaPage, 1500);
        }
    }, 1);
};

captchaResponse=fnc;
setInterval(fnc, 500);
initCaptchaPage();
setTimeout(refreshStats, 1000);

setInterval(function() {
    timer--;
    if(timer < 0) {
        $('#timer').text('Refreshing captcha...');
        setTimeout(initCaptchaPage, 1000);
        setTimeout(refreshStats, 1000);
    } else {
        $('#timer').html('<strong>' + timer.toString() + '</strong> seconds until refresh.');
    }
}, 1000);
