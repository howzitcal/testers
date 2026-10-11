FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn -q -DskipTests package

FROM eclipse-temurin:21-jre
WORKDIR /app
RUN mkdir -p /app/data
COPY --from=build /app/target/springboot-app-0.0.1-SNAPSHOT.jar /app/app.jar
EXPOSE 8001
ENV SPRING_DATASOURCE_URL=jdbc:sqlite:/app/data/leads.db
VOLUME ["/app/data"]
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
