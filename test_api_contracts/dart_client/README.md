# Forge Client

Client Dart généré automatiquement par Forge AGI pour consommer l'API.

## Installation

```bash
cd dart_client
dart pub get
```

## Utilisation

```dart
import 'package:forge_client/forge_client.dart';

void main() async {
  final client = ForgeClient(baseUrl: 'http://localhost:8000');
  
  try {
    // Vérifier la santé de l'API
    final health = await client.health();
    print('API Status: ${health.status}');
    
    // Utiliser les endpoints des entités
    // ... (voir les méthodes disponibles dans forge_client.dart)
    
  } catch (e) {
    print('Erreur: $e');
  } finally {
    client.dispose();
  }
}
```

## Endpoints disponibles

- `GET /health` - Vérification de santé

- `GET /users` - Liste des users
- `POST /users` - Créer un user
- `GET /users/{id}` - Récupérer un user
- `PUT /users/{id}` - Mettre à jour un user
- `DELETE /users/{id}` - Supprimer un user

- `GET /restaurants` - Liste des restaurants
- `POST /restaurants` - Créer un restaurant
- `GET /restaurants/{id}` - Récupérer un restaurant
- `PUT /restaurants/{id}` - Mettre à jour un restaurant
- `DELETE /restaurants/{id}` - Supprimer un restaurant

- `GET /bookings` - Liste des bookings
- `POST /bookings` - Créer un booking
- `GET /bookings/{id}` - Récupérer un booking
- `PUT /bookings/{id}` - Mettre à jour un booking
- `DELETE /bookings/{id}` - Supprimer un booking

## Modèles de données

Les modèles sont générés automatiquement avec support JSON.
Utilisez `fromJson()` pour désérialiser et `toJson()` pour sérialiser.

## Gestion des erreurs

Le client lève des exceptions en cas d'erreur HTTP.
Gérez-les avec try/catch dans votre code.
