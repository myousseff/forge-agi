import 'dart:convert';
import 'package:http/http.dart' as http;

// Modèles de données
class User {
  User({
    required this.email,
    required this.displayName,
  });

  final String email;
  final String displayName;

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      email: json['email'] as String,
      displayName: json['displayName'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'email': email,
      'displayName': displayName,
    };
  }
}

class UserList {
  UserList({
    required this.data,
    required this.total,
    required this.page,
    required this.limit,
  });

  final String data;
  final int total;
  final int page;
  final int limit;

  factory UserList.fromJson(Map<String, dynamic> json) {
    return UserList(
      data: json['data'] as String,
      total: json['total'] as int,
      page: json['page'] as int,
      limit: json['limit'] as int,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'data': data,
      'total': total,
      'page': page,
      'limit': limit,
    };
  }
}

class Restaurant {
  Restaurant({
    required this.title,
    required this.address,
    required this.seats,
    required this.phone,
  });

  final String title;
  final String address;
  final int seats;
  final String phone;

  factory Restaurant.fromJson(Map<String, dynamic> json) {
    return Restaurant(
      title: json['title'] as String,
      address: json['address'] as String,
      seats: json['seats'] as int,
      phone: json['phone'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      'address': address,
      'seats': seats,
      'phone': phone,
    };
  }
}

class RestaurantList {
  RestaurantList({
    required this.data,
    required this.total,
    required this.page,
    required this.limit,
  });

  final String data;
  final int total;
  final int page;
  final int limit;

  factory RestaurantList.fromJson(Map<String, dynamic> json) {
    return RestaurantList(
      data: json['data'] as String,
      total: json['total'] as int,
      page: json['page'] as int,
      limit: json['limit'] as int,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'data': data,
      'total': total,
      'page': page,
      'limit': limit,
    };
  }
}

class Booking {
  Booking({
    required this.userId,
    required this.restaurantId,
    required this.date,
    required this.partySize,
  });

  final String userId;
  final String restaurantId;
  final String date;
  final int partySize;

  factory Booking.fromJson(Map<String, dynamic> json) {
    return Booking(
      userId: json['userId'] as String,
      restaurantId: json['restaurantId'] as String,
      date: json['date'] as String,
      partySize: json['partySize'] as int,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'userId': userId,
      'restaurantId': restaurantId,
      'date': date,
      'partySize': partySize,
    };
  }
}

class BookingList {
  BookingList({
    required this.data,
    required this.total,
    required this.page,
    required this.limit,
  });

  final String data;
  final int total;
  final int page;
  final int limit;

  factory BookingList.fromJson(Map<String, dynamic> json) {
    return BookingList(
      data: json['data'] as String,
      total: json['total'] as int,
      page: json['page'] as int,
      limit: json['limit'] as int,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'data': data,
      'total': total,
      'page': page,
      'limit': limit,
    };
  }
}

class ForgeClient {
  final String baseUrl;
  final http.Client _httpClient;

  ForgeClient({
    this.baseUrl = 'http://localhost:8000',
    http.Client? httpClient,
  }) : _httpClient = httpClient ?? http.Client();

  // Endpoints système
  Future<HealthResponse> health() async {
    final response = await _httpClient.get(
      Uri.parse('$baseUrl/health'),
    );

    if (response.statusCode == 200) {
      return HealthResponse.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Erreur de santé: ${response.statusCode}');
    }
  }

  // Endpoints User
  Future<List<User>> getusers() async {
    final response = await _httpClient.get(
      Uri.parse('$baseUrl/users'),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return (data['data'] as List)
          .map((json) => User.fromJson(json))
          .toList();
    } else {
      throw Exception('Erreur récupération users: ${response.statusCode}');
    }
  }

  Future<User> getUser(String id) async {
    final response = await _httpClient.get(
      Uri.parse('$baseUrl/users/$id'),
    );

    if (response.statusCode == 200) {
      return User.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Erreur récupération User: ${response.statusCode}');
    }
  }

  Future<User> createUser(User user) async {
    final response = await _httpClient.post(
      Uri.parse('$baseUrl/users'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(user.toJson()),
    );

    if (response.statusCode == 200) {
      return User.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Erreur création User: ${response.statusCode}');
    }
  }

  Future<User> updateUser(String id, User user) async {
    final response = await _httpClient.put(
      Uri.parse('$baseUrl/users/$id'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(user.toJson()),
    );

    if (response.statusCode == 200) {
      return User.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Erreur mise à jour User: ${response.statusCode}');
    }
  }

  Future<void> deleteUser(String id) async {
    final response = await _httpClient.delete(
      Uri.parse('$baseUrl/users/$id'),
    );

    if (response.statusCode != 200) {
      throw Exception('Erreur suppression User: ${response.statusCode}');
    }
  }

  // Endpoints Restaurant
  Future<List<Restaurant>> getrestaurants() async {
    final response = await _httpClient.get(
      Uri.parse('$baseUrl/restaurants'),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return (data['data'] as List)
          .map((json) => Restaurant.fromJson(json))
          .toList();
    } else {
      throw Exception('Erreur récupération restaurants: ${response.statusCode}');
    }
  }

  Future<Restaurant> getRestaurant(String id) async {
    final response = await _httpClient.get(
      Uri.parse('$baseUrl/restaurants/$id'),
    );

    if (response.statusCode == 200) {
      return Restaurant.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Erreur récupération Restaurant: ${response.statusCode}');
    }
  }

  Future<Restaurant> createRestaurant(Restaurant restaurant) async {
    final response = await _httpClient.post(
      Uri.parse('$baseUrl/restaurants'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(restaurant.toJson()),
    );

    if (response.statusCode == 200) {
      return Restaurant.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Erreur création Restaurant: ${response.statusCode}');
    }
  }

  Future<Restaurant> updateRestaurant(String id, Restaurant restaurant) async {
    final response = await _httpClient.put(
      Uri.parse('$baseUrl/restaurants/$id'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(restaurant.toJson()),
    );

    if (response.statusCode == 200) {
      return Restaurant.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Erreur mise à jour Restaurant: ${response.statusCode}');
    }
  }

  Future<void> deleteRestaurant(String id) async {
    final response = await _httpClient.delete(
      Uri.parse('$baseUrl/restaurants/$id'),
    );

    if (response.statusCode != 200) {
      throw Exception('Erreur suppression Restaurant: ${response.statusCode}');
    }
  }

  // Endpoints Booking
  Future<List<Booking>> getbookings() async {
    final response = await _httpClient.get(
      Uri.parse('$baseUrl/bookings'),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return (data['data'] as List)
          .map((json) => Booking.fromJson(json))
          .toList();
    } else {
      throw Exception('Erreur récupération bookings: ${response.statusCode}');
    }
  }

  Future<Booking> getBooking(String id) async {
    final response = await _httpClient.get(
      Uri.parse('$baseUrl/bookings/$id'),
    );

    if (response.statusCode == 200) {
      return Booking.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Erreur récupération Booking: ${response.statusCode}');
    }
  }

  Future<Booking> createBooking(Booking booking) async {
    final response = await _httpClient.post(
      Uri.parse('$baseUrl/bookings'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(booking.toJson()),
    );

    if (response.statusCode == 200) {
      return Booking.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Erreur création Booking: ${response.statusCode}');
    }
  }

  Future<Booking> updateBooking(String id, Booking booking) async {
    final response = await _httpClient.put(
      Uri.parse('$baseUrl/bookings/$id'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(booking.toJson()),
    );

    if (response.statusCode == 200) {
      return Booking.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Erreur mise à jour Booking: ${response.statusCode}');
    }
  }

  Future<void> deleteBooking(String id) async {
    final response = await _httpClient.delete(
      Uri.parse('$baseUrl/bookings/$id'),
    );

    if (response.statusCode != 200) {
      throw Exception('Erreur suppression Booking: ${response.statusCode}');
    }
  }

  void dispose() {
    _httpClient.close();
  }
}