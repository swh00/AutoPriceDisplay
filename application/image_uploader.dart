// File: lib/image_uploader.dart
import 'dart:io';
import 'package:http/http.dart' as http;

class ImageUploader {
  final String token;

  ImageUploader({required this.token});

  Future<bool> uploadImage(File imageFile) async {
    final uri = Uri.parse('http://34.64.216.79/api/analyze/');
    final request = http.MultipartRequest('POST', uri);

    // 인증 토큰 추가
    request.headers['Authorization'] = 'Token $token';

    // 이미지 파일 추가
    request.files.add(
      await http.MultipartFile.fromPath('image', imageFile.path),
    );

    try {
      final response = await request.send();

      if (response.statusCode == 200 || response.statusCode == 201) {
        print('Image uploaded and analyzed successfully.');
        final responseBody = await response.stream.bytesToString();
        print(responseBody);
        return true;
      } else {
        print('Failed to analyze image. Status code: ${response.statusCode}');
        final respStr = await response.stream.bytesToString();
        print('Server response: $respStr');
        return false;
      }
    } catch (e) {
      print('Error uploading image: $e');
      return false;
    }
  }
}
