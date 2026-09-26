package com.unifiedai.backend.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(name = "citizen_profiles")
public class CitizenProfileEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "profile_id")
    private Integer profileId;

    @Column(name = "citizen_id", nullable = false, unique = true, length = 64)
    private String citizenId;

    @Column(length = 100)
    private String state;

    @Column(length = 100)
    private String district;

    @Column(name = "annual_income", precision = 12, scale = 2)
    private BigDecimal annualIncome;

    @Column(length = 100)
    private String occupation;

    @Column(length = 50)
    private String category;

    @Column(name = "is_taxpayer", nullable = false)
    private boolean isTaxpayer = false;

    @Column(name = "has_dpiit_recognition", nullable = false)
    private boolean hasDpiitRecognition = false;

    @Column(name = "business_incorporated_years")
    private Integer businessIncorporatedYears;

    @Column(name = "landholding_acres", precision = 6, scale = 2)
    private BigDecimal landholdingAcres;

    @Column(name = "is_differently_abled", nullable = false)
    private boolean isDifferentlyAbled = false;

    @Column(name = "disability_percentage", precision = 5, scale = 2)
    private BigDecimal disabilityPercentage;

    @Column(name = "additional_attributes", columnDefinition = "json")
    private String additionalAttributes;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt = Instant.now();

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "citizen_id", referencedColumnName = "citizen_id", insertable = false, updatable = false)
    private CitizenEntity citizen;

    public CitizenProfileEntity() {}

    public CitizenProfileEntity(String citizenId) {
        this.citizenId = citizenId;
        this.updatedAt = Instant.now();
    }

    @PreUpdate
    public void onUpdate() {
        this.updatedAt = Instant.now();
    }

    public Integer getProfileId() {
        return profileId;
    }

    public void setProfileId(Integer profileId) {
        this.profileId = profileId;
    }

    public String getCitizenId() {
        return citizenId;
    }

    public void setCitizenId(String citizenId) {
        this.citizenId = citizenId;
    }

    public String getState() {
        return state;
    }

    public void setState(String state) {
        this.state = state;
    }

    public String getDistrict() {
        return district;
    }

    public void setDistrict(String district) {
        this.district = district;
    }

    public BigDecimal getAnnualIncome() {
        return annualIncome;
    }

    public void setAnnualIncome(BigDecimal annualIncome) {
        this.annualIncome = annualIncome;
    }

    public String getOccupation() {
        return occupation;
    }

    public void setOccupation(String occupation) {
        this.occupation = occupation;
    }

    public String getCategory() {
        return category;
    }

    public void setCategory(String category) {
        this.category = category;
    }

    public boolean isTaxpayer() {
        return isTaxpayer;
    }

    public void setTaxpayer(boolean taxpayer) {
        isTaxpayer = taxpayer;
    }

    public boolean isHasDpiitRecognition() {
        return hasDpiitRecognition;
    }

    public void setHasDpiitRecognition(boolean hasDpiitRecognition) {
        this.hasDpiitRecognition = hasDpiitRecognition;
    }

    public Integer getBusinessIncorporatedYears() {
        return businessIncorporatedYears;
    }

    public void setBusinessIncorporatedYears(Integer businessIncorporatedYears) {
        this.businessIncorporatedYears = businessIncorporatedYears;
    }

    public BigDecimal getLandholdingAcres() {
        return landholdingAcres;
    }

    public void setLandholdingAcres(BigDecimal landholdingAcres) {
        this.landholdingAcres = landholdingAcres;
    }

    public boolean isDifferentlyAbled() {
        return isDifferentlyAbled;
    }

    public void setDifferentlyAbled(boolean differentlyAbled) {
        isDifferentlyAbled = differentlyAbled;
    }

    public BigDecimal getDisabilityPercentage() {
        return disabilityPercentage;
    }

    public void setDisabilityPercentage(BigDecimal disabilityPercentage) {
        this.disabilityPercentage = disabilityPercentage;
    }

    public String getAdditionalAttributes() {
        return additionalAttributes;
    }

    public void setAdditionalAttributes(String additionalAttributes) {
        this.additionalAttributes = additionalAttributes;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(Instant updatedAt) {
        this.updatedAt = updatedAt;
    }

    public CitizenEntity getCitizen() {
        return citizen;
    }

    public void setCitizen(CitizenEntity citizen) {
        this.citizen = citizen;
    }
}
