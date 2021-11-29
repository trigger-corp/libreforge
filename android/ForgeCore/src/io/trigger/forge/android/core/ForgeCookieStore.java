package io.trigger.forge.android.core;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.Vector;

import org.apache.http.client.CookieStore;
import org.apache.http.cookie.Cookie;
import org.apache.http.impl.cookie.BasicClientCookie;

import android.net.Uri;
import android.webkit.CookieManager;

public class ForgeCookieStore implements CookieStore {
    private String url;

    public ForgeCookieStore(String url) {
        this.url = url;
    }

    @Override
    public void addCookie(Cookie cookie) {
        StringBuilder cookieStr = new StringBuilder();
        cookieStr.append(cookie.getName()).append("=").append(cookie.getValue());
        if (cookie.getDomain() != null) {
            cookieStr.append("; Domain=" + cookie.getDomain());
        }
        if (cookie.getPath() != null) {
            cookieStr.append("; Path=" + cookie.getPath());
        }
        if (cookie.getExpiryDate() != null) {
            SimpleDateFormat df = new SimpleDateFormat("dd MMM yyyy HH:mm:ss", Locale.US);
            String asGmt = df.format(cookie.getExpiryDate().getTime()) + " GMT";
            cookieStr.append("; Expires=" + asGmt);
        }

        CookieManager.getInstance().setCookie(url, cookieStr.toString());
    }

    @Override
    public void clear() {
        CookieManager.getInstance().removeAllCookie();
    }

    @Override
    public boolean clearExpired(Date date) {
        CookieManager.getInstance().removeExpiredCookie();
        return true;
    }

    @Override
    public List<Cookie> getCookies() {
        Vector<Cookie> cookieList = new Vector<Cookie>();
        String cookies = CookieManager.getInstance().getCookie(url);
        if (cookies != null) {
            for (String cookie : cookies.split(", ")) {
                String[] parts = cookie.split("=", 2);
                BasicClientCookie basicCookie = new BasicClientCookie(parts[0], parts[1]);
                basicCookie.setDomain(Uri.parse(url).getHost());
                cookieList.add(basicCookie);
            }
        }
        return cookieList;
    }

}
