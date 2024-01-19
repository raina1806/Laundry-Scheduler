// App.js
import React, { useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import GoogleAuth from './GoogleAuth';

const App = () => {
  const [userInfo, setUserInfo] = useState(null);

  const handleGoogleLogin = (authResult) => {
   
    setUserInfo(authResult);
  };

  return (
    <View style={styles.container}>
      {userInfo ? (
        <View>
          <Text>Welcome, {userInfo.user.name}!</Text>
        </View>
      ) : (
        <GoogleAuth onLogin={handleGoogleLogin} />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default App;
