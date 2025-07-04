//File: lib/login_manager.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class LoginManager {
  final String username;
  final String password;

  LoginManager({required this.username, required this.password});

  // 로그인 및 JWT 토큰 발급
  Future<String?> login() async {
    final uri = Uri.parse('http://34.64.216.79/api/login/');
    final response = await http.post(
      uri,
      body: {
        'username': username,
        'password': password,
      },
    );
    print(response.body);
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return data['token']; // JWT 토큰 반환
    } else {
      //return 'test_token'; // 로그인 실패 시 테스트용 토큰 반환
      return null; // 로그인 실패 시 null 반환
    }
  }
}
