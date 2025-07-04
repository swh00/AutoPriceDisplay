import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'login_manager.dart';
import 'image_upload_page.dart';

class LoginPage extends StatefulWidget {
  @override
  _LoginPageState createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final TextEditingController _usernameController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  bool _isLoading = false;
  bool _saveCredentials = false;

  @override
  void initState() {
    super.initState();
    _loadSavedCredentials();
  }

  Future<void> _loadSavedCredentials() async {
    final prefs = await SharedPreferences.getInstance();
    final savedUsername = prefs.getString('username');
    final savedPassword = prefs.getString('password');
    final saveChecked = prefs.getBool('save_credentials') ?? false;

    if (saveChecked) {
      setState(() {
        _usernameController.text = savedUsername ?? '';
        _passwordController.text = savedPassword ?? '';
        _saveCredentials = true;
      });
    }
  }

  Future<void> _login() async {
    setState(() {
      _isLoading = true;
    });

    final username = _usernameController.text;
    final password = _passwordController.text;

    final loginManager = LoginManager(username: username, password: password);
    final token = await loginManager.login();

    setState(() {
      _isLoading = false;
    });

    if (token != null) {
      // 저장
      final prefs = await SharedPreferences.getInstance();
      if (_saveCredentials) {
        await prefs.setString('username', username);
        await prefs.setString('password', password);
        await prefs.setBool('save_credentials', true);
      } else {
        await prefs.remove('username');
        await prefs.remove('password');
        await prefs.setBool('save_credentials', false);
      }

      // 이동
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => ImageUploadPage(token: token),
        ),
      );
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('로그인 성공! 🎉'),
        backgroundColor: Colors.green,
      ));
    } else {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('로그인 실패. 아이디/비밀번호 확인해주세요.'),
        backgroundColor: Colors.red,
      ));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 32.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.lock_outline,
                  size: 100, color: Colors.blueAccent),
              const SizedBox(height: 16),
              const Text(
                'Welcome Back!',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  color: Colors.blueAccent,
                ),
              ),
              const SizedBox(height: 40),
              TextField(
                controller: _usernameController,
                decoration: InputDecoration(
                  labelText: 'Username',
                  prefixIcon: const Icon(Icons.person),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
              const SizedBox(height: 20),
              TextField(
                controller: _passwordController,
                obscureText: true,
                decoration: InputDecoration(
                  labelText: 'Password',
                  prefixIcon: const Icon(Icons.lock),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
              const SizedBox(height: 10),
              CheckboxListTile(
                title: const Text('ID/비밀번호 저장'),
                value: _saveCredentials,
                onChanged: (value) {
                  setState(() {
                    _saveCredentials = value ?? false;
                  });
                },
                controlAffinity: ListTileControlAffinity.leading,
              ),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _login,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blueAccent,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: _isLoading
                      ? const CircularProgressIndicator(
                          valueColor:
                              AlwaysStoppedAnimation<Color>(Colors.white),
                        )
                      : const Text(
                          'Login',
                          style: TextStyle(fontSize: 18),
                        ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
