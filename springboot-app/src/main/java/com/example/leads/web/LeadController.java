package com.example.leads.web;

import com.example.leads.model.Lead;
import com.example.leads.repository.LeadRepository;
import com.example.leads.service.WelcomeEmailService;
import jakarta.validation.Valid;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
@RequestMapping("/")
public class LeadController {

    private final LeadRepository leadRepository;
    private final WelcomeEmailService welcomeEmailService;

    public LeadController(LeadRepository leadRepository, WelcomeEmailService welcomeEmailService) {
        this.leadRepository = leadRepository;
        this.welcomeEmailService = welcomeEmailService;
    }

    @GetMapping
    public String list(Model model) {
        model.addAttribute("leads", leadRepository.findAll());
        return "leads/list";
    }

    @GetMapping("/leads/new")
    public String createForm(Model model) {
        model.addAttribute("lead", new Lead());
        model.addAttribute("title", "New Lead");
        return "leads/form";
    }

    @PostMapping("/leads")
    public String create(@Valid @ModelAttribute("lead") Lead lead,
                         BindingResult result,
                         Model model,
                         RedirectAttributes redirectAttributes) {
        if (result.hasErrors()) {
            model.addAttribute("title", "New Lead");
            return "leads/form";
        }
        Lead saved = leadRepository.save(lead);
        welcomeEmailService.sendWelcomeEmail(saved);
        redirectAttributes.addFlashAttribute("message", "Lead created; welcome email queued.");
        return "redirect:/";
    }

    @GetMapping("/leads/{id}/edit")
    public String editForm(@PathVariable Long id, Model model) {
        Lead lead = leadRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Invalid lead id: " + id));
        model.addAttribute("lead", lead);
        model.addAttribute("title", "Edit Lead");
        return "leads/form";
    }

    @PostMapping("/leads/{id}")
    public String update(@PathVariable Long id,
                         @Valid @ModelAttribute("lead") Lead lead,
                         BindingResult result,
                         Model model,
                         RedirectAttributes redirectAttributes) {
        if (result.hasErrors()) {
            model.addAttribute("title", "Edit Lead");
            return "leads/form";
        }
        lead.setId(id);
        leadRepository.save(lead);
        redirectAttributes.addFlashAttribute("message", "Lead updated.");
        return "redirect:/";
    }

    @PostMapping("/leads/{id}/delete")
    public String delete(@PathVariable Long id, RedirectAttributes redirectAttributes) {
        leadRepository.deleteById(id);
        redirectAttributes.addFlashAttribute("message", "Lead deleted.");
        return "redirect:/";
    }
}
