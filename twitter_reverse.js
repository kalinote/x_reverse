/**
 * @file: twitter_reverse.js
 * @author Kalinote
 * @description 该脚本可以绕过SSL固定，并且捕捉对加密库的调用
 */

//#region 通用工具
function bin2ascii(array) {
    var result = [];

    for (var i = 0; i < array.length; ++i) {
        result.push(String.fromCharCode( // hex2ascii part
            parseInt(
                ('0' + (array[i] & 0xFF).toString(16)).slice(-2), // binary2hex part
                16
            )
        ));
    }
    return result.join('');
}

function bin2hex(array, length) {
    var result = "";

    length = length || array.length;

    for (var i = 0; i < length; ++i) {
        result += ('0' + (array[i] & 0xFF).toString(16)).slice(-2);
    }
    return result;
}
//#endregion

setTimeout(function () {
    Java.perform(function () {
        console.log("[.] Twitter分析脚本启动");

        //#region SSL固定绕过
        console.log("[.] 进行 SSL Pinning Bypass");

        /* 创建证书相关类 */
        var CertificateFactory = Java.use("java.security.cert.CertificateFactory");
        var FileInputStream = Java.use("java.io.FileInputStream");
        var BufferedInputStream = Java.use("java.io.BufferedInputStream");
        var X509Certificate = Java.use("java.security.cert.X509Certificate");
        var KeyStore = Java.use("java.security.KeyStore");
        var TrustManagerFactory = Java.use("javax.net.ssl.TrustManagerFactory");
        var SSLContext = Java.use("javax.net.ssl.SSLContext");
        
        /* 载入证书文件 */
        console.log("[+] 加载MITM CA证书")
        var cf = CertificateFactory.getInstance("X.509");

        try {
            var fileInputStream = FileInputStream.$new("/data/local/tmp/mitmproxy-ca-cert.crt");
        }
        catch (err) {
            console.log("[o] 发生错误: " + err);
        }

        var bufferedInputStream = BufferedInputStream.$new(fileInputStream);
        var ca = cf.generateCertificate(bufferedInputStream);
        bufferedInputStream.close();

        var certInfo = Java.cast(ca, X509Certificate);
        console.log("[o] MITM 证书CA信息: " + certInfo.getSubjectDN());

        // 创建KeyStore
        console.log("[+] 为MITM CA证书创建KeyStore");
        var keyStoreType = KeyStore.getDefaultType();
        var keyStore = KeyStore.getInstance(keyStoreType);
        keyStore.load(null, null);
        keyStore.setCertificateEntry("ca", ca);

        // 创建TrustManager
        console.log("[+] 为MITM CA证书创建可信任KeyStore的TruestManager");
        var tmfAlgorithm = TrustManagerFactory.getDefaultAlgorithm();
        var tmf = TrustManagerFactory.getInstance(tmfAlgorithm);
        tmf.init(keyStore);
        console.log("[+] TrustManager准备就绪");

        console.log("[+] 注入SSLContext方法")
        console.log("[-] 等待APP调用SSLContext.init")

        SSLContext.init.overload("[Ljavax.net.ssl.KeyManager;", "[Ljavax.net.ssl.TrustManager;", "java.security.SecureRandom").implementation = function (a, b, c) {
            console.log("[o] App 调用 SSLContext.init");
            SSLContext.init.overload("[Ljavax.net.ssl.KeyManager;", "[Ljavax.net.ssl.TrustManager;", "java.security.SecureRandom").call(this, a, tmf.getTrustManagers(), c);
            console.log("[+] SSLContext 初始化自定义 TrustManager");
        }

        //#endregion

        //#region HMAC-SHA1加密算法监听
        console.log("[+] 监听HMAC-SHA1加密算法:")
        var Mac = Java.use('javax.crypto.Mac');
        var SecretKeySpec = Java.use('javax.crypto.spec.SecretKeySpec')
        Mac.getInstance.overload('java.lang.String').implementation = function(algorithm) {
            console.log("[o] 正在使用算法: " + algorithm);
            return this.getInstance(algorithm);
        };

        SecretKeySpec.$init.overload('[B', 'java.lang.String').implementation = function(key, spec) {
            console.log("[o] 检测到密钥: " + bin2hex(key) + " | " + bin2ascii(key));
            return this.$init(key, spec);
        };

        Mac.doFinal.overload('[B').implementation = function(input) {
            console.log("[o] 检测到Base String: " + bin2ascii(input));
            var result = this.doFinal(input);

            var Base64 = Java.use('java.util.Base64');
            var encoder = Base64.getEncoder();
            var result_base64 = encoder.encodeToString(result);

            console.log("[o] 生成的签名: " + result_base64);
            return result;
        };
        //#endregion

    });
}, 0);
