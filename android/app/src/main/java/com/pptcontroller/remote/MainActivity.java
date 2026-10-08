package com.pptcontroller.remote;

import android.content.Context;
import android.content.SharedPreferences;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Build;
import android.os.Bundle;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.view.KeyEvent;
import android.view.View;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity implements SensorEventListener {

    private WebView webView;
    private EditText inputServerIp;
    private Button btnConnect;
    private SharedPreferences prefs;
    private Vibrator vibrator;

    private SensorManager sensorManager;
    private Sensor rotationSensor;
    private Sensor gyroSensor;
    private boolean isGyroRunning = false;
    private final float[] rotationMatrix = new float[9];
    private final float[] orientationAngles = new float[3];

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

        // Hardware sensor initialization
        sensorManager = (SensorManager) getSystemService(Context.SENSOR_SERVICE);
        if (sensorManager != null) {
            rotationSensor = sensorManager.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR);
            if (rotationSensor == null) {
                rotationSensor = sensorManager.getDefaultSensor(Sensor.TYPE_ORIENTATION);
            }
            gyroSensor = sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE);
        }

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

        webView.addJavascriptInterface(new Object() {
            @JavascriptInterface
            public boolean isSupported() {
                return rotationSensor != null || gyroSensor != null;
            }

            @JavascriptInterface
            public void start() {
                runOnUiThread(() -> startGyroSensors());
            }

            @JavascriptInterface
            public void stop() {
                runOnUiThread(() -> stopGyroSensors());
            }
        }, "AndroidSensors");
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

        // Call triggerNav (with debounce) or remoteWS in WebView
        final String script = "if (window.triggerNav) { window.triggerNav('" + action + "'); } else if (window.remoteWS) { window.remoteWS.sendAction('" + action + "'); }";
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

    private long lastSensorDispatchTime = 0;
    private float accumulatedDx = 0f;
    private float accumulatedDy = 0f;

    private void startGyroSensors() {
        if (sensorManager != null && !isGyroRunning) {
            isGyroRunning = true;
            accumulatedDx = 0f;
            accumulatedDy = 0f;
            lastSensorDispatchTime = android.os.SystemClock.uptimeMillis();
            if (gyroSensor != null) {
                sensorManager.registerListener(this, gyroSensor, SensorManager.SENSOR_DELAY_GAME);
            } else if (rotationSensor != null) {
                sensorManager.registerListener(this, rotationSensor, SensorManager.SENSOR_DELAY_GAME);
            }
        }
    }

    private void stopGyroSensors() {
        if (sensorManager != null && isGyroRunning) {
            isGyroRunning = false;
            sensorManager.unregisterListener(this);
        }
    }

    @Override
    public void onSensorChanged(SensorEvent event) {
        if (!isGyroRunning || webView == null) return;

        if (event.sensor.getType() == Sensor.TYPE_GYROSCOPE) {
            // In phone portrait pointing towards presentation screen:
            // - Horizontal panning (left/right) is rotation around Z-axis (values[2])
            // - Vertical tilting (up/down) is rotation around X-axis (values[0])
            float dx = -event.values[2] * 2.5f;
            float dy = -event.values[0] * 2.5f;

            accumulatedDx += dx;
            accumulatedDy += dy;

            long now = android.os.SystemClock.uptimeMillis();
            if (now - lastSensorDispatchTime >= 20) { // ~50Hz smooth updates
                final float sendX = accumulatedDx;
                final float sendY = accumulatedDy;
                accumulatedDx = 0f;
                accumulatedDy = 0f;
                lastSensorDispatchTime = now;
                final String js = "if (window.onNativeGyroDelta) window.onNativeGyroDelta(" + sendX + ", " + sendY + ");";
                webView.post(() -> webView.evaluateJavascript(js, null));
            }
        } else if (event.sensor.getType() == Sensor.TYPE_ROTATION_VECTOR) {
            SensorManager.getRotationMatrixFromVector(rotationMatrix, event.values);
            SensorManager.getOrientation(rotationMatrix, orientationAngles);
            // orientationAngles: [0] = azimuth/yaw (rad), [1] = pitch (rad)
            float yawDeg = (float) Math.toDegrees(orientationAngles[0]);
            float pitchDeg = (float) Math.toDegrees(orientationAngles[1]);
            final String js = "if (window.onNativeOrientation) window.onNativeOrientation(" + yawDeg + ", " + pitchDeg + ");";
            webView.post(() -> webView.evaluateJavascript(js, null));
        }
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {}

    @Override
    protected void onPause() {
        super.onPause();
        stopGyroSensors();
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
