# PRD: Real-time Emotion Detection System

**Version**: 1.0.0 | **Status**: Implemented | **Date**: 2026-03-16

---

## 1. Problem Statement

A data scientist needs a production-ready system to detect and log human emotions in real-time from a webcam feed, with full user management, data persistence, and analytics capabilities.

## 2. User Stories

| ID   | As a…          | I want to…                                     | So that…                                   |
| ---- | -------------- | ---------------------------------------------- | ------------------------------------------ |
| US-1 | Researcher     | see real-time emotion labels on detected faces | I can observe reactions during experiments |
| US-2 | Analyst        | query historical emotion logs per session      | I can do offline analysis                  |
| US-3 | Admin          | manage user accounts with role-based access    | I can control who accesses data            |
| US-4 | Data Scientist | get emotion score distributions via REST API   | I can feed results to downstream models    |

## 3. Functional Requirements

| FR    | Feature                            | Status  |
| ----- | ---------------------------------- | ------- |
| FR-1  | User Registration                  |  Done |
| FR-2  | User Login (OAuth2 password flow)  |  Done |
| FR-3  | Access Token Validation            |  Done |
| FR-4  | Token Refresh with Rotation        |  Done |
| FR-5  | Protected Route Middleware         |  Done |
| FR-6  | Role-Based Access Control (RBAC)   |  Done |
| FR-7  | Secure Password Storage (bcrypt)   |  Done |
| FR-8  | User Logout (token revocation)     |  Done |
| FR-9  | Real-time WebSocket emotion stream |  Done |
| FR-10 | Face detection (MTCNN)             |  Done |
| FR-11 | Emotion analysis (DeepFace)        |  Done |
| FR-12 | Session + EmotionLog persistence   |  Done |
| FR-13 | REST API: sessions & analytics     |  Done |

## 4. Non-Functional Requirements

- **Latency**: WebSocket round-trip < 200ms per frame on local hardware
- **Accuracy**: face detection confidence ≥ 0.85 (MTCNN threshold)
- **Security**: JWT HS256, bcrypt cost-12, refresh token rotation
- **Scalability**: async I/O throughout, pluggable PostgreSQL for multi-user
- **Observability**: structured JSON logging, Prometheus metrics endpoint

## 5. Out of Scope (v1)

- GPU acceleration
- Multi-camera streams
- Face recognition / identity tracking across sessions
