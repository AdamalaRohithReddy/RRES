package com.unifiedai.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Map;

public class UserProfileDto {

    @JsonProperty("citizen_id")
    private String citizenId;

    private String name;

    @JsonProperty("date_of_birth")
    private LocalDate dateOfBirth;

    private Integer age;
    private String gender;
    private String phone;

    private String state;
    private String district;

    @JsonProperty("annual_income")
    private BigDecimal annualIncome;

    private String occupation;
    private String category;

    @JsonProperty("is_taxpayer")
    private Boolean isTaxpayer;

    @JsonProperty("has_dpiit_recognition")
    private Boolean hasDpiitRecognition;

    @JsonProperty("business_incorporated_years")
    private Integer businessIncorporatedYears;

    @JsonProperty("landholding_acres")
    private BigDecimal landholdingAcres;

    @JsonProperty("is_differently_abled")
    private Boolean isDifferentlyAbled;

    @JsonProperty("disability_percentage")
    private BigDecimal disabilityPercentage;

    @JsonProperty("additional_attributes")
    private Map<String, Object> additionalAttributes;

    public UserProfileDto() {}

    public String getCitizenId() {
        return citizenId;
    }

    public void setCitizenId(String citizenId) {
        this.citizenId = citizenId;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public LocalDate getDateOfBirth() {
        return dateOfBirth;
    }

    public void setDateOfBirth(LocalDate dateOfBirth) {
        this.dateOfBirth = dateOfBirth;
    }

    public Integer getAge() {
        return age;
    }

    public void setAge(Integer age) {
        this.age = age;
    }

    public String getGender() {
        return gender;
    }

    public void setGender(String gender) {
        this.gender = gender;
    }

    public String getPhone() {
        return phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
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

    public Boolean getIsTaxpayer() {
        return isTaxpayer;
    }

    public void setIsTaxpayer(Boolean taxpayer) {
        isTaxpayer = taxpayer;
    }

    public Boolean getHasDpiitRecognition() {
        return hasDpiitRecognition;
    }

    public void setHasDpiitRecognition(Boolean hasDpiitRecognition) {
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

    public Boolean getIsDifferentlyAbled() {
        return isDifferentlyAbled;
    }

    public void setIsDifferentlyAbled(Boolean differentlyAbled) {
        isDifferentlyAbled = differentlyAbled;
    }

    public BigDecimal getDisabilityPercentage() {
        return disabilityPercentage;
    }

    public void setDisabilityPercentage(BigDecimal disabilityPercentage) {
        this.disabilityPercentage = disabilityPercentage;
    }

    public Map<String, Object> getAdditionalAttributes() {
        return additionalAttributes;
    }

    public void setAdditionalAttributes(Map<String, Object> additionalAttributes) {
        this.additionalAttributes = additionalAttributes;
    }
}
