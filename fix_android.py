import os

filepath = r"C:\Users\Administrator\Desktop\Local_APK_Store\Client_App\app\src\main\java\com\elitesoftware\appmarketplace\MainActivity.java"

with open(filepath, "r") as f:
    content = f.read()

# Replace imports
content = content.replace("import androidx.appcompat.app.AppCompatActivity;", "import android.app.Activity;\nimport android.net.wifi.WifiManager;\nimport android.content.Context;")
content = content.replace("extends AppCompatActivity", "extends Activity")

# Replace ActionBar logic
content = content.replace("if (getSupportActionBar() != null) getSupportActionBar().hide();", 
                          "if (getActionBar() != null) getActionBar().hide();")

# Replace Cert logic
content = content.replace("intent.putExtra(android.security.KeyChain.EXTRA_CERTIFICATE, certBytes);",
                          "intent.putExtra(android.security.KeyChain.EXTRA_PKCS12, certBytes);")

# Add Multicast lock logic
multicast_logic = '''
            WifiManager wifi = (WifiManager) getApplicationContext().getSystemService(Context.WIFI_SERVICE);
            WifiManager.MulticastLock lock = null;
            if (wifi != null) {
                lock = wifi.createMulticastLock("EliteMarketplaceDiscovery");
                lock.acquire();
            }
            try (DatagramSocket socket = new DatagramSocket()) {
'''
content = content.replace("try (DatagramSocket socket = new DatagramSocket()) {", multicast_logic)

multicast_release = '''
            } catch (Exception e) {
                e.printStackTrace();
            }
            if (lock != null && lock.isHeld()) {
                lock.release();
            }
'''
content = content.replace("} catch (Exception e) {\n                e.printStackTrace();\n            }", multicast_release)


with open(filepath, "w") as f:
    f.write(content)

