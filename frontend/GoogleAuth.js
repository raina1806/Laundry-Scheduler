// components/GoogleAuth.js
import React, { useState } from 'react';
import { View, Button, Alert, ActivityIndicator, StyleSheet } from 'react-native';
import { authorize } from 'react-native-app-auth';

const GoogleAuth = ({ onLogin }) => {
  const [loading, setLoading] = useState(false);

  const config = {
    issuer: 'https://accounts.google.com',
    clientId: '576064921101-143ppscb1ru7tfs97lh5r9gg7p2dle7d.apps.googleusercontent.com', 
    redirectUrl: 'http://localhost:8000', 
    scopes: ['openid', 'profile', 'email'],
  };

  const handleLogin = async () => {
    try {
      setLoading(true);
      const result = await authorize(config);
      onLogin(result);
    } catch (error) {
      Alert.alert('Authentication Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  const sendAuthorizationCodeToBackend = async (authorizationCode) => {
    try {
      const response = await fetch('http://127.0.0.1:8000/auth/google', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code: authorizationCode }),
      });
  
      // Handle the response as needed
      const data = await response.json();
      console.log('Backend response:', data);
    } catch (error) {
      console.error('Error sending authorization code to backend:', error);
    }
  };
  

  return (
    <View style={styles.container}>
      <Button title="Login with Google" onPress={handleLogin} disabled={loading} />
      {loading && <ActivityIndicator size="small" color="#0000ff" />}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginTop: 20,
  },
});

export default GoogleAuth;
