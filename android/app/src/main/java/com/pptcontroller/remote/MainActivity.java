package com.pptcontroller.remote;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Build;
import android.os.Bundle;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.view.KeyEvent;
import android.view.View;
import android.view.WindowManager;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {

    private WebView webView;
    private EditText inputServerIp;
    private Button btnConnect;
    private SharedPreferences prefs;
    private Vibrator vibrator;

    private static final String PREF_NAME = "PPT_REMOTE_PREFS";
    private static final String KEY_SERVER_IP = "server_ip";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Keep screen on during presentation
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        vibrator = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
        prefs = getSharedPreferences(PREF_NAME, MODE_PRIVATE);

        inputServerIp = findViewById(R.id.input_server_ip);
        btnConnect = findViewById(R.id.btn_connect);
        Button btnModeUsb = findViewById(R.id.btn_mode_usb);
        Button btnModeWifi = findViewById(R.id.btn_mode_wifi);
        webView = findViewById(R.id.webview);

        setupWebView();

        String savedIp = prefs.getString(KEY_SERVER_IP, "127.0.0.1:8765");
        inputServerIp.setText(savedIp);

        btnConnect.setOnClickListener(v -> {
            String ip = inputServerIp.getText().toString().trim();
            if (!ip.isEmpty()) {
                loadServer(ip);
            }
        });

        btnModeUsb.setOnClickListener(v -> {
            inputServerIp.setText("127.0.0.1:8765");
            loadServer("127.0.0.1:8765");
        });

        btnModeWifi.setOnClickListener(v -> {
            inputServerIp.setText("192.168.0.7:8765");
            loadServer("192.168.0.7:8765");
        });

        // Automatically connect on launch with saved IP
        if (!savedIp.isEmpty()) {
            loadServer(savedIp);
        }
    }

    private void setupWebView() {
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        settings.setCacheMode(WebSettings.LOAD_NO_CACHE);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                Toast.makeText(MainActivity.this, "Terhubung ke Controller", Toast.LENGTH_SHORT).show();
            }

            @Override
            public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
                Toast.makeText(MainActivity.this, "Gagal terhubung: " + description, Toast.LENGTH_LONG).show();
            }
        });

        webView.setWebChromeClient(new WebChromeClient());
    }

    private void loadServer(String serverAddress) {
        if (!serverAddress.startsWith("http://") && !serverAddress.startsWith("https://")) {
            serverAddress = "http://" + serverAddress;
        }

        prefs.edit().putString(KEY_SERVER_IP, inputServerIp.getText().toString().trim()).apply();
        webView.loadUrl(serverAddress);
    }

    private void triggerAction(String action) {
        android.util.Log.d("MainActivity", "triggerAction: " + action);
        // Haptic feedback
        if (vibrator != null && vibrator.hasVibrator()) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator.vibrate(VibrationEffect.createOneShot(35, VibrationEffect.DEFAULT_AMPLITUDE));
            } else {
                vibrator.vibrate(35);
            }
        }

        // Call remoteWS.sendAction in WebView
        final String script = "if (window.remoteWS) { window.remoteWS.sendAction('" + action + "'); }";
        webView.post(() -> webView.evaluateJavascript(script, val -> {
            android.util.Log.d("MainActivity", "evaluateJavascript (" + action + ") result: " + val);
        }));
    }

    @Override
    public boolean dispatchKeyEvent(KeyEvent event) {
        int keyCode = event.getKeyCode();
        if (keyCode == KeyEvent.KEYCODE_VOLUME_UP) {
            if (event.getAction() == KeyEvent.ACTION_DOWN && event.getRepeatCount() == 0) {
                triggerAction("next");
            }
            return true; // Completely consume event and suppress system volume
        } else if (keyCode == KeyEvent.KEYCODE_VOLUME_DOWN) {
            if (event.getAction() == KeyEvent.ACTION_DOWN && event.getRepeatCount() == 0) {
                triggerAction("prev");
            }
            return true; // Completely consume event and suppress system volume
        }
        return super.dispatchKeyEvent(event);
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_VOLUME_UP || keyCode == KeyEvent.KEYCODE_VOLUME_DOWN) {
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    @Override
    public boolean onKeyUp(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_VOLUME_UP || keyCode == KeyEvent.KEYCODE_VOLUME_DOWN) {
            return true;
        }
        return super.onKeyUp(keyCode, event);
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
