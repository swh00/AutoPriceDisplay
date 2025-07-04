//File: lib/image_picker_manager.dart
import 'dart:io';
import 'package:image_picker/image_picker.dart';
import 'package:image_cropper/image_cropper.dart';
import 'package:flutter/material.dart';

class ImagePickerManager {
  final ImagePicker _picker = ImagePicker();

  Future<File?> pickAndCropImage(BuildContext context) async {
    // 사용자에게 선택지 제공
    final source = await showDialog<ImageSource>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('이미지 선택'),
        content: Text('이미지를 선택할 방법을 골라주세요.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, ImageSource.camera),
            child: Text('카메라'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, ImageSource.gallery),
            child: Text('갤러리'),
          ),
        ],
      ),
    );

    if (source == null) return null;

    final pickedFile = await _picker.pickImage(source: source);
    if (pickedFile == null) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('이미지를 선택하지 않았습니다.'),
        backgroundColor: Colors.orange,
      ));
      return null;
    }

    final croppedFile = await ImageCropper().cropImage(
      sourcePath: pickedFile.path,
      compressFormat: ImageCompressFormat.jpg,
      compressQuality: 90,
      uiSettings: [
        AndroidUiSettings(
          toolbarTitle: '이미지 자르기',
          toolbarColor: Colors.blue,
          toolbarWidgetColor: Colors.white,
          hideBottomControls: false,
          lockAspectRatio: false,
        ),
        IOSUiSettings(
          title: '이미지 자르기',
        ),
      ],
    );

    return croppedFile != null ? File(croppedFile.path) : null;
  }
}
