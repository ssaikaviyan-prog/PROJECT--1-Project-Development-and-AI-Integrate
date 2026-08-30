package com.project.security.service;

import com.project.security.model.User;
import com.project.security.repository.UserRepository;
import com.project.security.security.JwtService;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

@Service
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;

    public AuthService(UserRepository userRepository, PasswordEncoder passwordEncoder, JwtService jwtService) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
    }

    public String register(String username, String password) {
        // Validate unique username
        if (userRepository.findByUsername(username).isPresent()) {
            throw new IllegalArgumentException("Username '" + username + "' is already taken.");
        }

        // Hash password with BCrypt
        String encodedPassword = passwordEncoder.encode(password);

        // Save new user with default role 'USER'
        User user = new User(username, encodedPassword, "USER");
        userRepository.save(user);

        // Generate JWT token
        return jwtService.generateToken(username, user.getRole());
    }

    public String login(String username, String password) {
        // Fetch user from database
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new IllegalArgumentException("Invalid username or password."));

        // Match hashed password
        if (!passwordEncoder.matches(password, user.getPassword())) {
            throw new IllegalArgumentException("Invalid username or password.");
        }

        // Generate JWT token
        return jwtService.generateToken(username, user.getRole());
    }

    public Map<String, Object> validateToken(String token) {
        Map<String, Object> response = new HashMap<>();
        
        if (jwtService.isTokenValid(token)) {
            response.put("valid", true);
            response.put("username", jwtService.extractUsername(token));
            response.put("role", jwtService.extractRole(token));
        } else {
            response.put("valid", false);
            response.put("error", "Token is invalid or expired.");
        }
        
        return response;
    }
}
